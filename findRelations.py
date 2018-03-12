__author__ = 'ghamzak'

import re, os, sys, glob

ipath = 'SUMOtxt/*'

# Purpose: reads all the .kif files in a directory and retains all lines but comments in a list
# Path -> List
# Note: If you need all files in a path, it should end in *, e.g. 'SUMOtxt/*'
def uncommentAndListAll(path):
    import glob, re
    files = glob.glob(path)
    container = []
    for fle in files:
        with open(fle, 'r') as f1:
            # remove comments and make list of lines
            med = [line.rstrip() for line in f1.readlines() if not re.match(r';', line)]
            for i, j in enumerate(med):
                if j:
                    container.append(j)
    container = re.split(r'(?<=\)) (?=\()', ' '.join(x for x in container))
    return container

# Purpose: Removes Semantic Predicates and other useless parts
# List -> List
def retainUsefulBlocks(entireList):
    useful = [x for x in entireList if not re.match(r'\t+|\s+|\?', x) and not re.match(r'\(=>', x) and not re.match(r'\(termFormat', x) and not re.match(r'\(synonymousExternalConcept', x)]
    return useful

# don't lose term format
def retainUsefulBlocksTerm(entireList):
    useful = [x for x in entireList if not re.match(r'\t+|\s+|\?', x) and not re.match(r'\(=>', x) and not re.match(r'\(synonymousExternalConcept', x)]
    return useful

def findRelations(usefulList):
    predicates = [re.sub(r'\(', '', re.split(r' ', x)[0]) for x in usefulList]
    predicates = [x for x in predicates if not re.findall(r'[^a-zA-Z]', x)]  # and not re.findall(r'[^a-zA-Z]', x)
    predicates = sorted(list(set(predicates)))
    return predicates

# writes to a text file
def writeFile(filename,path):
    with open(filename, 'w') as tf:
        for i in findRelations(retainUsefulBlocks(uncommentAndListAll(path))):
            tf.write(i+'\n')

writeFile('RelationNames.txt',ipath)

# see = retainUsefulBlocks(uncommentAndListAll('SUMOtxt/*'))



