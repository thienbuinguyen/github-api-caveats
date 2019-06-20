"""
    This file contains functions to data crawl the API documents of Java (12)
    and extract all sentences containing caveat keywords to output json files.
"""

from bs4 import BeautifulSoup
import requests
import re
import glob
import os
import json
from nltk.tokenize import sent_tokenize

tree_url = 'https://docs.oracle.com/javase/12/docs/api/'
deprecated_url = 'https://docs.oracle.com/javase/12/docs/api/'

# Output file paths
api_tree_output_file = './output/java_api_12_entities.txt'
api_deprecated_output_file = './output/java_api_12_deprecated.txt'
api_text_output_dir = './api_text'
api_caveat_sentences_dir = './api_caveat_sentences'

keywords = ['insecure', 'susceptible', 'error', 'exception', 'null', 'susceptible',
        'unavailable', 'non thread safe','illegal', 'inappropriate', 'deprecate', 'better to', 'best to',
        'recommended', 'less desirable','discourage', 'instead of', 'rather than','otherwise',
        'do not', 'note that', 'notably', 'caution', 'under the condition', 'whether', 'if',
        'when', 'assume that', 'before', 'after', 'must', 'should', 'have to', 'need to', 'is not', 'are not',
        'was not', 'were not', 'will not', 'be not', 'does not', 'never', 'note', 'only', 'always']

def scrape_api_names(url, file_path):
    """ Find all Java class names from the Java hierarchy tree and write them to file. """
    tree_url = 'https://docs.oracle.com/en/java/javase/12/docs/api/overview-tree.html'
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, features='html.parser')
        print(soup)

        categories = soup.find_all('section', {'role': 'region'})
        apis = []
        for category in categories:
            items = category.find_all('li')

            for item in items:
                api_name = item.text.split('\n')[0].split(' ')[0]
                apis.append({'text': api_name, 'href': item.find('a').get('href')})

        with open(file_path, 'w') as f:
            for api in apis:
                f.write(api['text'].encode('utf-8') + ',' + api['href'].encode('utf-8') + '\n')
        print("Successfully scraped API tree!")
    except:
        print("Failed to scrape the API Tree at: {}".format(url))
        
def scrape_deprecated(url, output_file):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features='html.parser')
    cols = soup.find_all('th', {'class': 'colOne'}) # retrieve html relevant table header objects

    with open(output_file, 'w+') as f:
        try:
            for th in cols:
                a_element = th.find('a')
                link = a_element.get('href')
                name = a_element.text

                if link and name:
                    f.write(name.encode('utf-8') + ',' + link.encode('utf-8') + '\n')
            print("Successfully scraped deprecated entities!")
        except:
            print("Failed to scrape the deprecated entities at: {}".format(url))

def mine_api_html_recursive(file_path, output_dir):
    """ Retrieve the HTML pages for all classes and objects found from mine_api_names(). 
        The HTML pages for each class is saved locally.
    """
    try:
        with open(file_path) as f:
            for line in f:
                line = line.strip().split(',')
                api = line[0]
                api_url = base_url + line[1]
                r = requests.get(api_url)
                with open(output_dir + '/' + api + '.html', 'w') as output_f:
                    output_f.write(r.text.encode('utf-8'))
        print("Successfully extracted all API text!")
    except Exception as e:
        print("Failed to extract API text!")
        print(e)

def extract_api_caveats(html_file):
    """ Extract sentences that contain a caveat keyword within an API HTML file. """
    soup = BeautifulSoup(open(html_file), features='html.parser')
    methods = soup.find_all('li', {'class': 'blockList'})
    class_desc = soup.find('div', {'class': 'description'})
    api_caveats = []

    if class_desc:
        desc = class_desc.find('div', {'class': 'block'})
        caveat_sentences = []
        if desc:
            sentences = sent_tokenize(desc.text)
            for sentence in sentences:
                for keyword in keywords:
                    matches = re.search(r'\b' + keyword + r'\b', sentence, re.IGNORECASE)
                    if matches:
                        caveat_sentences.append(sentence)
                        break

            if caveat_sentences:
                api_caveats.append({'class_level_caveat_sentences': caveat_sentences})

    for method in methods:
        name = method.find('h4')
        desc = method.find('div', {'class': 'block'})

        if method.find('h3'):
            continue

        if name and desc:
            sentences = sent_tokenize(desc.text)
            caveat_sentences = []
            misc = method.find_all('dd')
            caveat_misc = []

            for sentence in sentences:
                sentence = ' '.join(sentence.split())
                for keyword in keywords:
                    matches = re.search(r'\b' + keyword + r'\b', sentence, re.IGNORECASE)
                    if matches:
                        caveat_sentences.append(sentence)
                        break

            for m in misc:
                text = ' '.join(m.text.split())
                for keyword in keywords:
                    matches = re.search(r'\b'+ keyword + r'\b', text, re.IGNORECASE)
                    if matches:
                        caveat_misc.append(text)
                        break

            if caveat_sentences or caveat_misc:
                api_caveats.append({'name': name.text, 'caveat_sentences': caveat_sentences, 'caveat_misc': caveat_misc})

    return api_caveats

def extract_all_api_caveat_sentences():
    files = [f for f in glob.glob(api_text_output_dir + '/*')]
    num_class_level_caveats = 0
    num_sentence_caveats = 0
    num_misc_caveats = 0

    for file in files:
        api_caveats = extract_api_caveats(file)
        name = os.path.splitext(os.path.basename(file))[0]

        for api_caveat in api_caveats:
            if 'class_level_caveat_sentences' in api_caveat:
                num_class_level_caveats += len(api_caveat['class_level_caveat_sentences'])
            else:
                num_sentence_caveats += len(api_caveat['caveat_sentences']) 
                num_misc_caveats += len(api_caveat['caveat_misc'])

        if len(api_caveats) == 0:
            print("No API caveat sentences found for: " + file)
        else:
            with open(api_caveat_sentences_dir + '/' + name + '.json', 'w+') as f:
                json.dump(api_caveats, f)
            print('Extracted API caveat sentences from: ' + file)

    print('Found {} class level caveats, {} method sentence caveats and {} misc caveats ({} total)'.format(num_class_level_caveats, num_sentence_caveats, num_misc_caveats, num_class_level_caveats + num_sentence_caveats + num_misc_caveats))

# scrape_api_names(tree_url, api_tree_output_file)
# scrape_deprecated(deprecated_url, api_deprecated_output_file)
