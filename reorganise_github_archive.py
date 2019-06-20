""" 
    Reorganise '.gz' files downloaded from GitHub Archive in the CWD into folders by month.
    Instructions for downloading the data is provided at https://www.gharchive.org/
"""

import os
import glob

os.chdir("./github-archive")

files = [file for file in glob.glob("*.gz")]
print("Reorganising {} files.".format(len(files)))

for file in files:
    name = "-".join(os.path.splitext(file)[0].split("-")[:2])
    if not os.path.isdir(name):
        os.makedirs(name)

    os.rename(file, os.path.join(name, file))
