import requests
import json
import os
import re
import nltk
import glob

base_url = 'https://api.github.com/repos/'
git_token = os.environ['TOKEN']
headers = {'Authorization': 'token %s' % git_token}

def clean_commit(commit):
    if 'html_url' in commit and 'commit' in commit:
        return {
                'html_url': commit['html_url'],
                'message': commit['commit']['message'],
                'comment_count': commit['commit']['comment_count'],
                'date': commit['commit']['author']['date']
                }

def clean_issue(issue):
    if 'title' in issue and 'body' in issue and 'id' in issue and \
        'html_url' in issue and 'comments' in issue:
        return {
                'title': issue['title'],
                'body': issue['body'],
                'id': issue['id'],
                'html_url': issue['html_url'],
                'comments': issue['comments'],
                }

def clean_issue_comment(comment):
    if 'html_url' in comment and 'body' in comment and 'id' in comment:
        return {
                'html_url': comment['html_url'],
                'body': comment['body'],
                'id': comment['id']
                }

def clean(arr, func):
    ret = []
    for e in arr:
        cleaned = func(e)
        if cleaned:
            ret.append(cleaned)
    return ret

def traverse_paginated_responses(url):
    params = {'per_page':100, 'state':'all'}
    r = requests.get(url, params=params, headers=headers)
    json_obj = r.json()

    # print the number of pages to traverse
    if 'last' in r.links:
        pages = re.search('&page=(.*)', r.links['last']['url']) 
        if pages:
            print('Traversing {} pages...'.format(pages.group(1)))

    while 'next' in r.links.keys():
        r = requests.get(r.links['next']['url'], headers=headers)
        json_obj.extend(r.json())
    return json_obj

def retrieve_commits(url):
    commits_url = url + '/commits'
    return clean(traverse_paginated_responses(commits_url), clean_commit)

def retrieve_issues(url):
    issues_url = url + '/issues'
    return clean(traverse_paginated_responses(issues_url), clean_issue)

def retrieve_issue_comments(url):
    issue_comments_url  = url + '/issues/comments'
    return clean(traverse_paginated_responses(issue_comments_url), clean_issue_comment)

def retrieve_repo_artefacts(url):
    name = '-'.join(url.split('/')[-2:])

    # make the directory if needed
    path = os.getcwd()
    repo_path = path + '/repositories/' + name
    if not os.path.isdir(repo_path):
        os.mkdir(repo_path)

    with open(repo_path +  '/issues.json', 'w+') as issues_f, \
            open(repo_path + '/issue_comments.json', 'w+') as issue_comments_f, \
            open(repo_path + '/commits.json', 'w+') as commits_f:

        json.dump(retrieve_issues(url), issues_f)
        json.dump(retrieve_issue_comments(url), issue_comments_f)
        json.dump(retrieve_commits(url), commits_f)

    print("Extracted all artefacts for {}!".format(name))

repos_to_extract = ['apache/incubator-dubbo']
def extract_repos(repos):
    for repo in repos_to_extract:
        if not os.path.isdir(os.getcwd() + '/repositories/' + repo):
            print("Extracting {}".format(repo))
            try:
                retrieve_repo_artefacts(base_url + repo)
            except e:
                print(e)

def extract_code_from_text(text):
    code_block_regex = r'```([^```]+?)```'
    inline_code_regex = r'`([^```]+?)`'

    code_blocks = re.findall(code_block_regex, text, re.DOTALL)
    text = re.sub(code_block_regex, '', text)
    sentences = nltk.sent_tokenize(text)
    inline_code = re.findall(inline_code_regex, text)
    
    return (sentences, code_blocks, inline_code)

def data_mine_sentences(obj):
    if 'body' in obj and obj['body']:
        sentences, code_blocks, inline_code = extract_code_from_text(obj['body'])
        obj.pop('body', None)
        obj['sentences'] = sentences
        obj['code_blocks'] = code_blocks
        obj['inline_code'] = inline_code
        return obj 

def data_mine_repos(repo_paths):
    for repo_path in repo_paths:
        with open(repo_path + '/issues.json', 'r') as issues_f, \
            open(repo_path + '/issue_comments.json', 'r') as issue_comments_f, \
            open(repo_path + '/issues_clean.json', 'w+') as issues_clean_f, \
            open(repo_path + '/issue_comments_clean.json', 'w+') as issues_comments_clean_f:

            issues_arr = json.load(issues_f)
            issue_comments_arr = json.load(issue_comments_f)

            issues_cleaned_arr = []
            issue_comments_cleaned_arr = []
            for e in issues_arr:
                data_mined_e = data_mine_sentences(e)
                if data_mined_e:
                    issues_cleaned_arr.append(data_mined_e)

            for e in issue_comments_arr:
                data_mined_e = data_mine_sentences(e)
                if data_mined_e:
                    issue_comments_cleaned_arr.append(data_mined_e)

            json.dump(issues_cleaned_arr, issues_clean_f)
            json.dump(issue_comments_cleaned_arr, issues_comments_clean_f)

            print('Data mined ' + repo_path)

def count_total_sentences():
    repos = glob.glob('./repositories/*')
    sentences = 0
    code_blocks = 0
    inline_code = 0
    for repo in repos:
        with open(repo + '/issues_clean.json') as issues_f, open(repo + '/issue_comments_clean.json') as issue_comments_f:
            issues_arr = json.load(issues_f)
            issue_comments_arr = json.load(issue_comments_f)

            for e in issues_arr:
                sentences += len(e['sentences'])
                code_blocks += len(e['code_blocks'])
                inline_code += len(e['inline_code'])

            for e in issue_comments_arr:
                sentences += len(e['sentences'])
                code_blocks += len(e['code_blocks'])
                inline_code += len(e['inline_code'])
            
    print('Sentences: {}'.format(sentences))
    print('Code blocks: {}'.format(code_blocks))
    print('Inline code: {}'.format(inline_code))

count_total_sentences()
