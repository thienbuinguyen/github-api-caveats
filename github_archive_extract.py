"""
Script to extract issues, issue comments, pull requests and pull request comments from .gz files from Github Archive.
Expects the '.gz' files in separate folders in the './github-archive' directory.
    e.g. Run 'wget https://data.gharchive.org/2018-{01..12}-{01..31}-{0..23}.json.gz' first.

    ./github-archive
        /2018-01/
            2018-01-01-1.json.gz
            ...
        /2018-02/
            2018-02-01-1.json.gz
            ...
Outputs the data as pickle files in the output_dir_path
"""

import ujson
import glob
import os
import gzip
import time
from itertools import repeat
from multiprocessing import Pool, cpu_count

archive_paths = glob.glob('/media/thien/Data Drive1/github-archive/*/')
ignore_paths = [
        '/media/thien/Data Drive1/github-archive/2019-01/',
        '/media/thien/Data Drive1/github-archive/2018-02/',
        '/media/thien/Data Drive1/github-archive/2018-03/',
        '/media/thien/Data Drive1/github-archive/2018-04/',
        '/media/thien/Data Drive1/github-archive/2018-05/',
        '/media/thien/Data Drive1/github-archive/2018-06/',
        '/media/thien/Data Drive1/github-archive/2018-07/',
        '/media/thien/Data Drive1/github-archive/2018-08/',
        '/media/thien/Data Drive1/github-archive/2018-09/',
        '/media/thien/Data Drive1/github-archive/2018-10/',
        '/media/thien/Data Drive1/github-archive/2018-11/',
        '/media/thien/Data Drive1/github-archive/2018-12/'
        ]
output_dir_path = '/media/thien/Data Drive1/github-archive-extracted-revised/'
java_repos_file_path = './repos.txt'
repo_names = None

def get_relevant_repo_names(file):
    repos = []

    with open(file) as f:
        for line in f:
            line = line.strip()
            repos.append(line)

    return set(repos)

# Extract issues, issue comments, pull requests and pull request comments for all .gz file in the given path
def extract_github_data(file, repo_names):
    issue_comments = []
    pull_request_comments = []
    corrupted = False

    try:
        with gzip.open(file, 'rb') as f_in:
            for line in f_in:
                try:
                    line = ujson.loads(line)
                     # only extract artefacts that are public and are part of a repo in the list of repo names
                    if 'public' in line and line["public"] and 'repo' in line and 'name' in line['repo'] and line['repo']['name'] in repo_names:
                        if "type" in line and line["type"] == "IssueCommentEvent": # extract comments
                            if line["payload"]["action"] == "created":
                                issue_comments.append({
                                    "body": line["payload"]["comment"]["body"],
                                    "issue": {
                                        "id": line["payload"]["issue"]["id"],
                                        "number": line["payload"]["issue"]["number"],
                                        "body": line["payload"]["issue"]["body"],
                                        "title": line["payload"]["issue"]["title"],
                                        "html_url": line["payload"]["issue"]["html_url"]
                                        },
                                    "repo_name": line["repo"]["name"],
                                    "html_url": line["payload"]["comment"]["html_url"]
                                    })
                        elif line["type"] == "PullRequestReviewCommentEvent": # Extract comments for pull requests
                            if line["payload"]["action"] == "created":
                                pull_request_comments.append({
                                    "body": line["payload"]["comment"]["body"],
                                    "diff_hunk": line["payload"]["comment"]["diff_hunk"],
                                    "html_url": line["payload"]["comment"]["html_url"],
                                    "pull_request_title": line["payload"]["pull_request"]["title"],
                                    "repo_name": line["repo"]["name"],
                                    })
                except:
                    pass # skip lines that can't be loaded or have missing keys
    except:
        corrupted = True

    obj = {"issue_comments": issue_comments, 
            "pull_request_comments": pull_request_comments,
            "corrupted": corrupted}

    try:
        file_name = os.path.basename(file)
        path = output_dir_path + file_name + '.json'
        with open(path, 'w+') as f:
            ujson.dump(obj, f)
    except:
        print("Failed to write {} to file".format(file))

def extract_all_github_data():
    start_time = time.time()
    p = Pool(8)

    repo_names = get_relevant_repo_names(java_repos_file_path)

    for path in archive_paths:
        if path in ignore_paths:
            continue
        print("Extracting directory {}".format(path))
        archive_files = [file for file in glob.glob(path + '*.gz')]
        data_lists = p.starmap(extract_github_data, zip(archive_files, repeat(repo_names)))

    print('Extraction completed in {} minutes.'.format((time.time() - start_time) / 60))

def combine_data():
    files = glob.glob(output_dir_path + '*.json')

    with open('./output/issue-comments-revised.jsonl', 'w+') as f_issue_out, \
            open('./output/pull-request-comments-revised.jsonl', 'w+') as f_pull_out,\
            open('./output/corrupted.txt', 'w+') as f_corrupt_out:

        for file in files:
            with open(file) as f:
                obj = ujson.load(f)

                for comment in obj['issue_comments']:
                    f_issue_out.write(ujson.dumps(comment) + '\n')

                for comment in obj['pull_request_comments']:
                    f_pull_out.write(ujson.dumps(comment) + '\n')

                if obj['corrupted']:
                    f_corrupt_out.write(file + '\n')

# extract_all_github_data()
combine_data()
