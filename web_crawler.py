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
deprecated_url = 'https://docs.oracle.com/en/java/javase/12/docs/api/deprecated-list.html'

# Output file paths
api_tree_output_file = './output/java_api_12_entities.txt'
api_deprecated_output_file = './output/java_api_12_deprecated.txt'
api_text_output_dir = '/media/thien/Data Drive1/java_api_12_text'
api_caveat_sentences_dir = './output/java_12_spec_caveat_sentences'

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
    sections = soup.find_all('section')
    class_desc = soup.find('div', {'class': 'description'})
    api_caveats = []

    # retrieve all sentences associated to the class
    caveat_sentences = []
    class_deprecated = False

    if class_desc:
        desc = class_desc.find('div', class_='block')
        if desc:
            class_deprecated = class_desc.find('div', class_='deprecationBlock', recursive=True) != None

            sentences = sent_tokenize(desc.text)
            for sentence in sentences:
                for keyword in keywords:
                    matches = re.search(r'\b' + keyword + r'\b', sentence, re.IGNORECASE)
                    if matches:
                        caveat_sentences.append(sentence)
                        break

    api_caveats.append({'class_level_caveat_sentences': caveat_sentences, 'deprecated': class_deprecated})

    for section in sections:
        first_a_element = section.find('a')
        
        if not first_a_element:
            continue
        
        section_type = ''
        a_id = first_a_element.get('id')        
        if a_id == 'field.detail':
            section_type = 'field'
        elif a_id == 'construtor.detail':
            section_type = 'constructor'
        elif a_id == 'method.detail':
            section_type = 'method'
        else: # skip all other sections
            continue 
        
        block_lists = section.find_all('li', class_='blockList')
        
        for api in block_lists:
            name = api.find('h4')
            desc = api.find('div', class_='block')
            signature = api.find('pre')

            # skip enclosing li elements for the sections
            if api.find('h3'):
                continue

            if name and desc and signature:
                signature_text = None
                if section_type == 'method':
                    signature_text = signature.text.replace('\u200b', '')
                    signature_text = signature_text.replace('\xa0', ' ')
                    signature_text = ' '.join(signature_text.split())
            
                deprecated = api.find('div', class_='deprecationBlock', recursive=True) != None
                caveat_obj = {
                    'name': name.text,
                    'type': section_type,
                    'signature': '' if deprecated else signature_text,
                    'deprecated': deprecated,
                    'caveat_sentences': [],
                    'caveat_misc': []
                }
                            
                sentences = sent_tokenize(desc.text)
                misc_list = api.find('dl')

                for sentence in sentences:
                    sentence = ' '.join(sentence.split())
                    for keyword in keywords:
                        matches = re.search(r'\b' + keyword + r'\b', sentence, re.IGNORECASE)
                        if matches:
                            caveat_obj['caveat_sentences'].append(sentence)
                            break

                if misc_list:
                    misc_text = []
                    curr_misc = ''
                    for e in misc_list:
                        if e.name == 'dt':
                            if curr_misc == '':
                                curr_misc = e.text
                                                 
                            # append the previous caveat misc data
                            if (len(misc_text) > 0):
                                caveat_obj['caveat_misc'].append({'misc_name': curr_misc, 'text': misc_text})
                        
                            misc_text = []
                            curr_misc = e.text
                        elif e.name == 'dd':
                            text = ' '.join(e.text.split()) # change any whitespace to single space
                            for keyword in keywords:
                                matches = re.search(r'\b'+ keyword + r'\b', text, re.IGNORECASE)
                                if matches:
                                    misc_text.append(text)
                                    break
                        
                    if len(misc_text) > 0:
                        caveat_obj['caveat_misc'].append({'misc_name': curr_misc, 'text': misc_text})

                api_caveats.append(caveat_obj)

    return api_caveats

def extract_all_api_caveat_sentences():
    files = [f for f in glob.glob(api_text_output_dir + '/*')]

    for file in files:
        api_caveats = extract_api_caveats(file)
        name = os.path.splitext(os.path.basename(file))[0]

        with open(api_caveat_sentences_dir + '/' + name + '.json', 'w+') as f:
            json.dump(api_caveats, f)

    print('Extraction complete!')

# scrape_deprecated(deprecated_url, api_deprecated_output_file)
extract_all_api_caveat_sentences()
