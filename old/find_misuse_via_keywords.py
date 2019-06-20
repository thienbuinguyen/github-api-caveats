import json
import os
import re
from java_api_tree_web_crawler import keywords

repo_path = './repositories'
repos = os.listdir(repo_path)

def get_array_elements_containing_keywords(arr, keywords, fields):
    ret = []

    for e in arr:
        keyword_found = False
        for keyword in keywords:
            for field in fields:
                if field in e and e[field] != None and re.search(r'\b' + keyword + r'\b', e[field].lower()):
                    keyword_found = True
                    break

            if keyword_found:
                break

        if keyword_found:
            ret.append(e)

    return ret

def search_repo_for_keywords(repo, keywords):
    with open(repo_path + '/' + repo + '/issues.json') as issues_f, \
            open(repo_path + '/' + repo + '/issue_comments.json') as issue_comments_f, \
            open(repo_path + '/' + repo + '/commits.json') as commits_f:

        issues = json.load(issues_f)
        issue_comments = json.load(issue_comments_f)
        commits = json.load(commits_f)

        potential_misuse_issues = get_array_elements_containing_keywords(issues, keywords, ['title', 'body']) 
        potential_misuse_issue_comments = get_array_elements_containing_keywords(issue_comments,keywords, ['body'])
        potential_misuse_commits = get_array_elements_containing_keywords(commits, keywords, ['message'])

        print(repo + ": Found {}/{} issues, {}/{} issue comments and {}/{} commits with a matching keyword" \
                .format(len(potential_misuse_issues), len(issues), len(potential_misuse_issue_comments), len(issue_comments), \
                len(potential_misuse_commits), len(commits)))

keywords_to_find = ['arrays', 'resultset']
print(keywords_to_find)
for repo in repos:
    search_repo_for_keywords(repo, keywords_to_find)
