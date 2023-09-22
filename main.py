import logging
import os

from colorama import Style, init
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from LongueuilQuebecScraper.spiders import LongueuilQuebecSpider

logger = logging.getLogger(__name__)


def main():
    init()

    settings = get_project_settings()

    data_file = settings.get('DATA_FILE')

    os.environ.setdefault('HTTP_PROXY', settings.get('HTTP_PROXY'))
    os.environ.setdefault('HTTPS_PROXY', settings.get('HTTP_PROXY'))

    process = CrawlerProcess(settings, install_root_handler=False)
    configure_logging()
    process.crawl(LongueuilQuebecSpider)
    process.start(install_signal_handlers=True)

    logger.info('SCRAPING COMPLETED.')


if __name__ == '__main__':
    main()
