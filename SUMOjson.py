__author__ = 'ghamzak'

import re, json
from findRelations import retainUsefulBlocks, uncommentAndListAll, retainUsefulBlocksTerm
ipath = 'SUMOtxt/*'

see = retainUsefulBlocks(uncommentAndListAll(ipath))

import pickle

def save_obj(obj, name):
    with open('obj/'+ name + '.pkl', 'wb+') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

save_obj(see, "see")

# see2 also contains termFormat, which is how it's expressed in English
see2 = retainUsefulBlocksTerm(uncommentAndListAll(ipath))

# see3 should be used to find wordnet mappings, by looking for (synonymousExternalConcept and (subsumingExternalConcept
see3 = uncommentAndListAll(ipath)

entities = [re.findall(r'(?<=\(documentation ).+(?= English)', x)[0] for x in see if re.findall(r'(?<=\(documentation ).+(?= English)', x)]
# result: there are currently 10992 entities defined/documented in SUMO


# now that we have all the entities in SUMO, we need to have an ID card for each, that says:
#   - this is my definition (DONE)
#   - these are my parents (DONE)
#   - these are my children (DONE)
#   - these are the classes mutually disjoint with me @partition@ (instances in me would never show up in the classes that are mutually disjoint with me)
#   - these are the domains where I show up >>> This could help in finding Qualia
#   - this is how I'm expressed in English (DONE)
#   - this is how I'm represented in WordNet (emailed Adam Pease); my guess: https://raw.githubusercontent.com/ontologyportal/sumo/master/WordNetMappings/WordNetMappings30-noun.txt
#   - here are some instances of me (you can see more in NELL) (my mistake, no such thing as instance in SUMO)
#   - and this is my pedigree (DONE)
#   - etc. (we can add to this list)


# returns the set of FOAFschema mappings
def findMapping(node):
    pattern = r'\(\w*ExternalConcept ".+" ' + node
    syn = [re.sub(r'"', r'', re.split(r' ', x)[1]) for x in see3 if re.search(pattern, x)]
    return syn


def findParents(node):
    # note: a node may have an arbitrary number of parents
    searchpattern = r'(?<=\(subclass )' + node + r' '
    parents = [re.sub(r'\)', r'', re.split(' ', x)[-1]) for x in see if re.search(searchpattern, x)]
    return parents

def findChildren(node):
    searchpattern = r'(?<=\(subclass ).+' + r'(?=\))'
    children = [re.split(' ',re.findall(searchpattern, x)[0])[0] for x in see if re.findall(searchpattern, x) and re.split(' ',re.findall(searchpattern, x)[0])[1] == node ]
    return children


def findDocumentation(node):
    searchpattern = r'\(documentation ' + node + r' EnglishLanguage\s*'
    doc = [re.sub(r'\)|\"', r'', re.sub(searchpattern, r'', x)) for x in see if re.match(searchpattern, x)]
    if doc:
        return doc[0]

def findTermFormat(node): # e.g. (termFormat EnglishLanguage pricePolicy "rate policy")
    searchpattern = r'\(termFormat EnglishLanguage\s*' + node + ' "'
    termFormat = [re.sub(r'[\"|\)]', r'', re.sub(searchpattern, '', x)) for x in see2 if re.search(searchpattern, x)]
    if termFormat:
        return termFormat[0]
    elif not re.findall(r' ', node):
        return node.lower()


# def findPartitions(node):  # e.g. (partition Physical Object Process)
#     return

# def findRelatedConcept(node): # e.g. (relatedInternalConcept HappyFacialExpression Smiling)
#     return


# finds a key in a possibly recursive dictionary data structure, returning its value
def _finditem(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        # print(k, v)
        if isinstance(v,dict):
            item = _finditem(v, key)
            if item is not None:
                # print(item)
                return item


def make_tree():
    tree = {}
    nodes = []
    rootNode = 'Entity'
    tree[rootNode] = {'documentation': findDocumentation(rootNode), 'Qualia': {}}
    if findTermFormat(rootNode):
        tree[rootNode]['EnglishFormat'] = findTermFormat(rootNode)
    stack = [rootNode]
    while stack:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
                # cur_node.add_child(child)
                curval = _finditem(tree,cur_node)
                if curval:
                    curval[child] = {}
                    curval[child]['Qualia'] = {}
                    if findDocumentation(child):
                        curval[child]['documentation'] = findDocumentation(child)
                    if findTermFormat(cur_node):
                        curval[child]['EnglishFormat'] = findTermFormat(child)
                print(child)
    return tree


# getting to find WN sense keys, using the files from SUMO GitHub page, WordNetMappings directory
wnpath = 'WN/*'
def uncommentAndListAll2(path):
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
    # container = re.split(r'(?<=\)) (?=\()', ' '.join(x for x in container))
    return container

NounVerb = uncommentAndListAll2(wnpath)
def findWNSenseKey(node):
    a = [i for i in NounVerb for x in re.split(' ', i) if x == '&%'+node+'=']
    sensekeys = []
    for sense in a:
        linesplit = re.split(' ', sense)
        try:
            d = int(linesplit[3])
            for j in range(0,int(linesplit[3])):
                sensekeyElements = []
                sensekeyElements.append(linesplit[2*j+4])
                sensekeyElements.append('%')
                if linesplit[2] == 'n':
                    sensekeyElements.append('1')
                elif linesplit[2] == 'v':
                    sensekeyElements.append('2')
                sensekeyElements.append(':')
                s = linesplit[1]
                if len(s) == 1:
                    s = '0' + s
                sensekeyElements.append(s)
                sensekeyElements.append(':')
                f = linesplit[2*j+5]
                if len(f) == 1:
                    f = '0' + f
                sensekeyElements.append(f)
                x = ''.join(sensekeyElements)
                sensekeys.append(x)
        except:
            continue


    return sensekeys


# define a function which given a list of parents, finds the node in a tree
def findNode(parentslist, tree):
    # node = []
    for i in parentslist:
        tree = tree[i]
    node = tree
    return node

def sub(txt): return re.sub(r',', ' ', txt)




def make_csv():
    import csv
    csv1 = open('SUMOcsv-test1.csv', 'w')
    cw = csv.writer(csv1, delimiter = ',', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    tree = {}
    nodes = []
    rootNode = 'Entity'
    tree[rootNode] = {'documentation': findDocumentation(rootNode), 'Qualia': {}}
    if findTermFormat(rootNode):
        tree[rootNode]['EnglishFormat'] = findTermFormat(rootNode)
    stack = [rootNode]
    store = []
    temp = []
    while stack:
        cur_node = stack[0]
        if store:
            if findNode(store[-1], tree)['documentation'] and findNode(store[-1], tree)['EnglishFormat']:
                cw.writerow(store[-1]+[sub(findNode(store[-1], tree)['documentation']), findNode(store[-1], tree)['EnglishFormat']]+ findWNSenseKey(store[-1][-1]))
            elif findNode(store[-1], tree)['documentation'] and not findNode(store[-1], tree)['EnglishFormat']:
                cw.writerow(store[-1]+[sub(findNode(store[-1], tree)['documentation'])]+ findWNSenseKey(store[-1][-1]))
            elif findNode(store[-1], tree)['EnglishFormat'] and not findNode(store[-1], tree)['documentation']:
                cw.writerow(store[-1]+[sub(findNode(store[-1], tree)['EnglishFormat'])]+ findWNSenseKey(store[-1][-1]))
        stack = stack[1:]
        nodes.append(cur_node)
        print(cur_node)
        print(len(nodes))
        if temp:
            if store[-1][-1] in findParents(cur_node):
                temp = store[-1] + [cur_node]
            else:
                for s in store:
                    if s[-1] in findParents(cur_node):
                        temp = s + [cur_node]
        else:
            temp.append(cur_node)
        store.append(temp)
        print(store)
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
                curval = _finditem(tree,cur_node)
                if curval:
                    curval[child] = {}
                    curval[child]['Qualia'] = {}
                    if findDocumentation(child):
                        curval[child]['documentation'] = findDocumentation(child)
                    if findTermFormat(cur_node):
                        curval[child]['EnglishFormat'] = findTermFormat(child)
                print(child)
    csv1.close()
    return

seedecoded = [line.decode('utf-8').strip() for line in see]
save_obj(seedecoded, "seedecoded")



def findParents2(node):
    # note: a node may have an arbitrary number of parents
    # example: (subclass LiquidFood PreparedFood) >> findParents2(LiquidFood) returns PreparedFood
    searchpattern = r'(?<=\(subclass )' + node + r' '
    parents = [re.sub(r'\)', r'', re.split(' ', x)[-1]) for x in see if re.search(searchpattern, x)]
    return parents










