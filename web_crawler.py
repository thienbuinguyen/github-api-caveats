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
api_caveat_sentences_dir = './output/java_12_spec_caveat_sentences_revised'

keywords = ['insecure', 'susceptible', 'error', 'exception', 'null', 'susceptible',
        'unavailable', 'not thread safe','illegal', 'inappropriate', 'deprecate', 'better to', 'best to',
        'recommended', 'less desirable','discourage', 'instead of', 'rather than','otherwise',
        'do not', 'note that', 'notably', 'caution', 'under the condition', 'whether ', 'if ',
        'when ', 'assume that ', 'before', 'after', 'must', 'should', 'have to', 'need to', 
        'be not', 'never', 'none', 'only', 'always']

caveat_id = 0 # global counter to identify caveat objects
num_sentences = 0 # global counter for number of sentences analysed
num_caveat_sentences = 0 # global counter for caveat sentences

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

def extract_class_caveats(soup):
    global num_sentences

    class_deprecated = False
    desc = soup.find('div', class_='block')
    caveat_sentences = []
    if desc:
        class_deprecated = soup.find('div', class_='deprecationBlock', recursive=True) != None

        sentences = sent_tokenize(desc.text)
        num_sentences += len(sentences)
        for sentence in sentences:
            sentence = ' '.join(sentence.split()) # change any whitespace to single space
            for keyword in keywords:
                matches = re.search(keyword, sentence, re.IGNORECASE)
                if matches:
                    caveat_sentences.append(sentence)
                    break

    return {'class_caveat_sentences': caveat_sentences, 'deprecated': class_deprecated}

def calculate_section_type(soup):
    first_a_element = soup.find('a')
    section_type = ''
    if first_a_element:
        a_id = first_a_element.get('id')        
        if a_id == 'field.detail':
            section_type = 'field'
        elif a_id == 'constructor.detail':
            section_type = 'constructor'
        elif a_id == 'method.detail':
            section_type = 'method'

    return section_type

def extract_api_caveats(html_file):
    """ Extract sentences that contain a caveat keyword within an API HTML file. """
    global caveat_id
    global num_sentences
    global num_caveat_sentences

    soup = BeautifulSoup(open(html_file), features='html.parser')
    sections = soup.find_all('section')
    class_desc = soup.find('div', {'class': 'description'})
    api_caveats = []

    # retrieve all sentences associated to the class
    if class_desc:
        obj = extract_class_caveats(class_desc)
        obj['id'] = caveat_id
        api_caveats.append(obj)

        num_caveat_sentences += len(obj['class_caveat_sentences'])

    caveat_id += 1

    for section in sections:
        section_type = calculate_section_type(section) 
        # skip all sections that are not fields, constructors or methods
        if section_type == '':
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
                if section_type in ['method', 'constructor']:
                    signature_text = signature.text.replace('\u200b', '')
                    signature_text = signature_text.replace('\xa0', ' ')
                    signature_text = ' '.join(signature_text.split())
            
                deprecated = api.find('div', class_='deprecationBlock', recursive=True) != None
                caveat_obj = {
                    'name': name.text,
                    'type': section_type,
                    'signature': '' if deprecated else signature_text,
                    'deprecated': deprecated,
                    'sentences': [],
                    'caveat_misc': [],
                    'id': caveat_id
                }

                caveat_id += 1
                misc_list = api.find('dl')

                # extract misc sentences/text
                if misc_list:
                    curr_misc = ''
                    misc_objs = []

                    for e in misc_list:
                        if e.name == 'dt':
                            if curr_misc == '':
                                curr_misc = e.text
                                                 
                            # append the previous caveat misc data
                            if (len(misc_objs) > 0):
                                caveat_obj['caveat_misc'].append({'name': curr_misc, 'list': misc_objs})
                        
                            misc_objs = [] # reset list contents
                            curr_misc = e.text
                        elif e.name == 'dd':
                            text = ' '.join(e.text.split()) # change any whitespace to single space

                            # separate parameters and their caveat sentences
                            if curr_misc == 'Parameters:':
                                text_components = text.split(' - ')
                                sentences = sent_tokenize(' - '.join(text_components[1:]))

                                parameter_sentences = []
                                for sentence in sentences:
                                    for keyword in keywords:
                                        matches = re.search(keyword, sentence, re.IGNORECASE)
                                        if matches:
                                            parameter_sentences.append(sentence)
                                            break
                                misc_objs.append({'parameter': text_components[0], 'sentences': parameter_sentences})
                                num_caveat_sentences += len(parameter_sentences)
                                num_sentences += len(sentences)
                            # separate exceptions and their caveat sentences
                            elif curr_misc == 'Throws:':
                                text_components = text.split(' - ')
                                sentences = sent_tokenize(' - '.join(text_components[1:]))

                                exception_sentences = []
                                for sentence in sentences:
                                    for keyword in keywords:
                                        matches = re.search(keyword, sentence, re.IGNORECASE)
                                        if matches:
                                            exception_sentences.append(sentence)
                                            break
                                misc_objs.append({'exception': text_components[0], 'sentences': exception_sentences})
                                num_caveat_sentences += len(exception_sentences)
                                num_sentences += len(sentences)
                            else: # extract all other misc section sentences
                                sentences = sent_tokenize(text)

                                for sentence in sentences:
                                    for keyword in keywords:
                                        matches = re.search(keyword, sentence, re.IGNORECASE)
                                        if matches:
                                            misc_objs.append(sentence)
                                            break
                                num_caveat_sentences += len(misc_objs)
                                num_sentences += len(sentences)

                    # append the previous caveat misc data
                    if (len(misc_objs) > 0):
                        caveat_obj['caveat_misc'].append({'name': curr_misc, 'list': misc_objs})

                sentences = sent_tokenize(desc.text)
                num_sentences += len(sentences)

                for index, sentence in enumerate(sentences):
                    sentence = ' '.join(sentence.split())
                    
                    for keyword in keywords:
                        matches = re.search(keyword, sentence, re.IGNORECASE)
                        if matches:
                            caveat_obj['sentences'].append(sentence)
                            break

                num_caveat_sentences += len(caveat_obj['sentences'])
                api_caveats.append(caveat_obj)

    return api_caveats

def extract_all_api_caveat_sentences():
    global num_sentences
    global num_caveat_sentences
    
    num_sentences = 0
    num_caveat_sentences = 0
    files = [f for f in glob.glob(api_text_output_dir + '/*')]

    for file in files:
        print(file)
        api_caveats = extract_api_caveats(file)
        name = os.path.splitext(os.path.basename(file))[0]

        with open(api_caveat_sentences_dir + '/' + name + '.json', 'w+') as f:
            json.dump(api_caveats, f)

    print('Extraction complete!')
    print('Total number of sentences analysed: {}'.format(num_sentences))
    print('Total number of caveat sentences: {}'.format(num_caveat_sentences))

# scrape_deprecated(deprecated_url, api_deprecated_output_file)
extract_all_api_caveat_sentences()
