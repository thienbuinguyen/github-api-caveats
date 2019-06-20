from bs4 import BeautifulSoup
import requests

def scrape_deprecated(url, output_file):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features='lxml')
    cols = soup.find_all('th', {'class': 'colDeprecatedItemName'}) # retrieve html relevant table header objects

    with open('deprecated_java_api.txt', 'w') as f:
        for th in cols:
            a_element = th.find('a')
            link = a_element.get('href')
            name = a_element.text

            if link and name:
                f.write(name.encode('utf-8') + ',' + link.encode('utf-8') + '\n')

