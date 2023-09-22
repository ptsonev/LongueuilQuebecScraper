import re

import scrapy.utils.misc
from scrapy import Request, Selector, FormRequest
from scrapy.http import Response


class LongueuilQuebecSpider(scrapy.Spider):
    name = 'Longueuil Quebec'

    URL = 'https://www2.longueuil.quebec/fr/role/par-adresse'
    POST_URL = f'{URL}?ajax_form=1&_wrapper_format=drupal_ajax'

    DEFAULT_AJAX_REQUEST_HEADER = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    }

    def start_requests(self):
        yield Request(url=self.URL, callback=self.parse_ville)

    def parse_ville(self, response: Response):
        ville_options = self.parse_dropdown_values(response.css('#edit-ville'))
        for ville_name, ville in ville_options:
            ville_post_data = self.get_post_data(ville=ville)
            yield FormRequest(url=self.POST_URL,
                              formdata=ville_post_data,
                              cb_kwargs={
                                  'ville': (ville_name, ville)
                              },
                              headers=self.DEFAULT_AJAX_REQUEST_HEADER,
                              callback=self.parse_voie)

    def parse_voie(self, response: Response, **kwargs):
        html_selector = self.construct_html(response)

        roads = html_selector.xpath('.//input[normalize-space(@data-drupal-selector)="edit-roads"]/@value').getall()
        voie_list = self.parse_dropdown_values(html_selector.css('#edit-voie'))

        if len(roads) != 1:
            self.logger.error('more than one road.')

        elif not voie_list:
            self.logger.error('voie_list is empty.')

        else:
            # scrape here
            ville_name, ville = kwargs.get('ville')
            for voie_name, voie in voie_list:
                voie_post_data = self.get_post_data(ville=ville, voie=voie, roads=roads[0])
                yield FormRequest(url=self.POST_URL,
                                  formdata=voie_post_data,
                                  cb_kwargs={
                                      **kwargs,
                                      'voie': (voie_name, voie),
                                      'roads': roads[0],
                                  },
                                  headers=self.DEFAULT_AJAX_REQUEST_HEADER,
                                  callback=self.parse_type_de_voie)

    def parse_type_de_voie(self, response: Response, **kwargs):
        html_selector = self.construct_html(response)
        type_de_voie_list = self.parse_dropdown_values(html_selector.css('#edit-type-de-voie'))

        if len(type_de_voie_list) == 1:
            yield from self.parse_street_numbers(response=response, type_de_voie=type_de_voie_list[0], **kwargs)
        else:
            for type_de_voie_name, type_de_voie in type_de_voie_list:
                type_de_voie_post_data = self.get_post_data(type_de_voie=type_de_voie)
                yield FormRequest(url=self.POST_URL,
                                  formdata=type_de_voie_post_data,
                                  cb_kwargs={
                                      **kwargs,
                                      'type_de_voie': (type_de_voie_name, type_de_voie)
                                  },
                                  headers=self.DEFAULT_AJAX_REQUEST_HEADER,
                                  callback=self.parse_street_numbers)

    def parse_street_numbers(self, response: Response, **kwargs):
        html_selector = self.construct_html(response)

        street_numbers = self.parse_dropdown_values(html_selector.css('#edit-de'))
        type_de_voie_name, type_de_voie = kwargs.get('type_de_voie')

        results_post_data = self.get_post_data(type_de_voie=type_de_voie, street_numbers=street_numbers)
        yield FormRequest(url=self.POST_URL,
                          formdata=results_post_data,
                          cb_kwargs={
                              **kwargs,
                              'street_numbers': street_numbers,
                          },
                          headers=self.DEFAULT_AJAX_REQUEST_HEADER,
                          callback=self.download_listings)

    def download_listings(self, response: Response, **kwargs):
        html_selector = self.construct_html(response)
        listings = self.parse_dropdown_values(html_selector.css('#edit-liste'))
        if len(listings) == 1:
            yield from self.parse(response, liste=listings[0], **kwargs)
        else:
            for listing_name, listing in listings:
                listing_post_data = self.get_post_data(liste=listing)
                yield FormRequest(url=self.POST_URL,
                                  formdata=listing_post_data,
                                  cb_kwargs={
                                      **kwargs,
                                      'liste': (listing_name, listing),
                                  },
                                  headers=self.DEFAULT_AJAX_REQUEST_HEADER)

    def parse(self, response: Response, **kwargs):
        html_selector = self.construct_html(response)
        html = html_selector.get()
        street_name, street = kwargs.get('liste')

        if '<h2>Information sur la propriété</h2>' not in html or '</html>' not in html:
            self.logger.error(f'HTML error for {street}')

        all_fields = [
            'Numéro matricule',
            'Adresse',

            'Ville de',
            'Arrondissement',
            'Municipalité de',

            # 'En vigueur pour les exercices financiers',
            'Cadastre(s) et numéro(s) de lots',
            'Numéro de dossier',
            'Utilisation prédominante',
            "Numéro d'unité de voisinage",

            'Mesure frontale',
            'Superficie',
            "Nombre d'étages",
            'Année de construction',
            'Aire des étages',
            'Genre de construction',
            'Lien physique',
            'Nombre de logements',
            'Nombre de locaux non résidentiels',
            'Nombre de chambres locatives',
            'Date de référence au marché',
            'Valeur du terrain',
            'Valeur du bâtiment',
            "Valeur de l'immeuble",
            "Valeur de l'immeuble au rôle antérieur",
            "Catégorie et classe d'immeuble à des fins d'application des taux variés de taxation",
            "Valeur imposable de l'immeuble",
        ]

        owner_labels = [
            'Propriétaire',
            "Statut aux fins d'imposition scolaire",
            'Adresse postale',
            'Casier postal',
            "Condition particulière d'inscription",
            "Date d'inscription au rôle",
        ]

        current_result = {}
        for label in all_fields:
            value_selector = html_selector.xpath(f'//span[normalize-space(@class)="role-label" and normalize-space(text())="{label} :"]/following-sibling::span/b')
            if len(value_selector) != 1 and label in html:
                self.logger.error('More than one element returned. The website structure changed.')

            if label == 'Adresse':
                value = value_selector.xpath('a/text()').get(default='')
            else:
                value = ''.join(value_selector.xpath('.//text()').getall())

            current_result[label] = self.format_whitespaces(value)

        for index in range(1, 4):
            for owner_label in owner_labels:
                owner_selector = html_selector.xpath(f'//p[span[normalize-space(@class)="role-label" and normalize-space(text())="{owner_label} :"]][{index}]/span[2]/b')
                current_result[f'{owner_label}{index}'] = self.format_whitespaces(owner_selector.xpath('text()').get(default=''))

        yield current_result

    @staticmethod
    def format_whitespaces(input_string: str) -> str:
        if not input_string:
            return ''
        return re.sub('\s+', ' ', input_string).strip()

    @staticmethod
    def construct_html(response: Response) -> Selector:
        selectors = response.jmespath('[*]')
        data_list = [data.jmespath('data').get(default='') for data in selectors]
        return Selector(text='\n'.join(data_list))

    @staticmethod
    def parse_dropdown_values(input_selector: Selector) -> list[tuple[str, str]]:
        result = list()
        for option in input_selector.xpath('.//option'):
            option_name = option.xpath('text()').get()
            option_value = option.xpath('@value').get()
            if option_value and option_value != 'select':
                result.append((option_name, option_value))
        return result

    @staticmethod
    def get_post_data(ville: str = '', voie: str = '', roads: str = '', type_de_voie: str = '', street_numbers: list[tuple[str, str]] = None, liste: str = '') -> dict[str, str]:
        if liste:
            triggering_element = 'liste'

        elif street_numbers:
            triggering_element = 'op'

        elif type_de_voie:
            triggering_element = 'type_de_voie'

        elif voie:
            triggering_element = 'voie'

        else:
            triggering_element = 'ville'

        post_data = {
            'ville': ville,
            'voie': voie,
            'roads': roads,
            'type_de_voie': type_de_voie,
            'de': street_numbers[0][1] if street_numbers else '',
            'a': street_numbers[-1][1] if street_numbers else '',
            'form_build_id': '',
            'form_id': 'villong_consulter_par_adresse',
            '_triggering_element_name': triggering_element,
            '_drupal_ajax': '1',
            'ajax_page_state[theme]': 'bartikvl',
            'ajax_page_state[theme_token]': '',
            'ajax_page_state[libraries]': 'bartik/global-styling,bartikvl/global-styling,classy/base,classy/messages,core/drupal.ajax,core/html5shiv,core/jquery.form,core/normalize,system/base,villong_role_new/villong_role_new'
        }
        if liste:
            post_data['liste'] = liste

        return post_data
