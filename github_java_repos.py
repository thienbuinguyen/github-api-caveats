from github import Github
from datetime import datetime, timedelta
import json
from time import sleep
import os
import glob

g = Github(os.environ['TOKEN'], per_page=100)
output_dir = './output/repos/'
output_repo_name_file = './output/repos.txt'
query = 'language:java created:{}..{} stars:>=2'

def retrieve_repos():
    date = datetime(2009, 1, 1)
    count = 3

    for i in range(365 * 9):
        arr = []
        next = date + timedelta(days=1)

        try:
            repos = g.search_repositories(query.format(date.strftime('%Y-%m-%d'), 
                next.strftime('%Y-%m-%d')), sort='stars', order='desc')
            count -= 1

            for repo in repos:
                arr.append({
                    'name': repo.full_name,
                    'stars': repo.stargazers_count
                    })

            print('Writing repos for {}/{}/{} to file...'.format(date.day, date.month, date.year))
            with open(output_dir + str(date.day) + '-' + str(date.month) + '-' + str(date.year) + '-repos.json', 'w+') as f:
                json.dump(arr, f)
        except:
            print("Failed for date: {}".format(date.strftime('%Y-%m-%d')))

        if count == 0:
            sleep(60)
            count = 3
        date = next

def extract_repo_names():
    """ Write all repo names to an output txt file """
    with open(output_repo_name_file, 'w+') as f:
        json_files = glob.glob(output_dir + '*.json')

        for file in json_files:
            with open(file) as json_file:
                arr = json.load(json_file)

                for obj in arr:
                    f.write(obj['name'] + '\n')

retrieve_repos()
# extract_repo_names()
