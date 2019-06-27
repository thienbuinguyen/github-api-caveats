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
Outputs the data as json files in './github-archive-extracted' directory.
"""

import json
import glob
import os
import gzip
import time
from multiprocessing import Pool
from tabulate import tabulate

archive_paths = glob.glob('/media/thien/Data Drive1/github-archive/*/')
ignore_paths = ['/media/thien/Data Drive1/github-archive/2019-01/']
output_dir_path = '/media/thien/Data Drive1/github-archive-extracted/'

# Extract issues, issue comments, pull requests and pull request comments for all .gz file in the given path
def extract_github_data(file):
    issues = []
    issue_comments = []
    pull_requests = []
    pull_request_comments = []
    last_line = ""
    error = None 

    print('Extracting {}'.format(file))
    try:
        with gzip.open(file, 'rb') as f_in:
            for line in f_in:
                last_line = line
                line = json.loads(line)
                if line["public"]: # only extract artefacts that are public
                    if line["type"] == "IssuesEvent": # extract issues
                        if line["payload"]["action"] == "opened":
                            issue_obj = line["payload"]["issue"]
                            issues.append({
                                "repo_name": line["repo"]["name"],
                                "number": issue_obj["number"],
                                "title": issue_obj["title"],
                                "body": issue_obj["body"],
                                "comments": issue_obj["comments"],
                                "html_url": issue_obj["html_url"]
                            })
                    elif line["type"] == "IssueCommentEvent": # extract comments
                        if line["payload"]["action"] == "created":
                            comment_obj = line["payload"]["comment"]
                            issue_comments.append({
                                "body": comment_obj["body"],
                                "issue_number": line["payload"]["issue"]["number"],
                                "repo_name": line["repo"]["name"],
                                "html_url": comment_obj["html_url"]
                            })
                    elif line["type"] == "PullRequestEvent": # extract pull request text
                        if line["payload"]["action"] == "opened":
                            pull_requests.append({
                                "number": line["payload"]["number"],
                                "title": line["payload"]["pull_request"]["title"],
                                "body": line["payload"]["pull_request"]["body"],
                                "repo_name": line["repo"]["name"],
                                "html_url": line["payload"]["pull_request"]["html_url"]
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
        error = {"file": file, "line": last_line}

    return {"issues": issues, 
            "issue_comments": issue_comments, 
            "pull_requests": pull_requests, 
            "pull_request_comments": pull_request_comments,
            "error": error}

def extract_all_github_data():
    start_time = time.time()
    p = Pool(10)
    num_files, num_issues, num_issue_comments, num_pull_requests,\
            num_pull_request_comments = 0, 0, 0, 0, 0
    errors = []

    for path in archive_paths:
        if path in ignore_paths:
            continue
        archive_files = [file for file in glob.glob(path + '*.gz')]
        num_files += len(archive_files)
        data_lists = p.map(extract_github_data, archive_files)

        issues = []
        issue_comments = []
        pull_requests = []
        pull_request_comments = []
        
        for data in data_lists:
            if data["error"]: # skip adding data if an error occured
                errors.append(data["error"])
                continue
            issues += data["issues"]
            issue_comments += data["issue_comments"]
            pull_requests += data["pull_requests"]
            pull_request_comments += data["pull_request_comments"]

        num_issues += len(issues)
        num_issue_comments += len(issue_comments)
        num_pull_requests += len(pull_requests)
        num_pull_request_comments += len(pull_request_comments)

        # Write extracted data to json files
        base_path = os.path.join(output_dir_path, os.path.basename(os.path.normpath(path)))
        with open(base_path + "-issues.json", "w+") as f_issues,\
                open(base_path + "-issue-comments.json", "w+") as f_issue_comments,\
                open(base_path + "-pull-requests.json", "w+") as f_pull_requests,\
                open(base_path + "-pull-request-comments.json", "w+") as f_pull_request_comments:
            json.dump(issues, f_issues)
            json.dump(issue_comments, f_issue_comments)
            json.dump(pull_requests, f_pull_requests)
            json.dump(pull_request_comments, f_pull_request_comments)

    print("\nExtraction Complete! Total of {} files mined.".format(num_files ))

    # Write any errors to a log file
    if errors:
        print("Note: A failure occured during extraction for one or more files. See 'github-extraction-log.txt' for more information.\n")
        with open("./github_extract_error_logs.txt", "a+") as f:
            for error in errors:
                f.write(str(error))

    # print total extracted data statistics
    print(tabulate([[num_issues, num_issue_comments, num_pull_requests, num_pull_request_comments]],
            headers=["issues", "issue comments", "pull requests", "pull request comments"]))
    print('Extraction completed in {} minutes.'.format((time.time() - start_time) / 60))

# extract_all_github_data()
