# LongueuilQuebecScraper

## Installing Python
1) Download and install Python<br/>
	32-bit Windows:<br/>
	https://www.python.org/ftp/python/3.11.0/python-3.11.0.exe<br/>
	
	64-bit Windows:<br/>
	https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe<br/>
	
	**Make sure to check the "Add python.exe to PATH" at the bottom of the installation window.**<br/>
	![image](https://drive.google.com/uc?export=view&id=1CqbfL0qezreCyh4GvQTOmwwILhPlwWnO)

## Installing the requirements
Open a command prompt and navigate to the scraper's directory.<br/> 
The easiest way is to open the scraper's folder and type cmd in the address bar.
![image](https://drive.google.com/uc?export=view&id=1MdOWMetTcP7cNo0YC9ZyLTFTU9fdEav1)
<br/>
Type the following command, you have to do this only once:<br/>
```
pip install -r requirements.txt
```

## Starting the scraper
You can start the scraper by typing the following command:<br/>
```
python main.py
```

# Proxy

The website doesn't have any anti-scraping protection.
But if you want you can add rotating proxy in LongueuilQuebecScraper/settings.py
set HTTPPROXY_ENABLED = True and HTTP_PROXY = 'http://username:password@host:port

# Caching

The caching is enabled, that way you can run the scraper over multiple session and it won't redownload the same records.
However, it isn't checking for duplicates, so delete the data.csv file each time you run it.
