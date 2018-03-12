__author__ = 'ghamzak'

import re, json
from SUMOjson import see, see2
from SUMOjson import findParents, findDocumentation, findTermFormat, _finditem, uncommentAndListAll2, findWNSenseKey, findNode, sub, findChildren
from QualiaExtraction import findTelic, findAgentive, findConstitutive

# wnpath = 'WN/*'
# NounVerb = uncommentAndListAll2(wnpath)


def make_csv():
    import csv
    csv1 = open('SUMOcsv-test8.csv', 'w')
    cw = csv.writer(csv1, delimiter = ',', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    tree = {}
    nodes = []
    rootNode = 'Entity'
    tree[rootNode] = {'documentation': findDocumentation(rootNode)}
    # if findTelic(rootNode):
    #     tree[rootNode]['Telic_Quale'] = findTelic(rootNode)
    # if findAgentive(rootNode):
    #     tree[rootNode]['Agentive_Quale'] = findAgentive(rootNode)
    # if findConstitutive(rootNode):
    #     tree[rootNode]['Constitutive_Quale'] = findConstitutive(rootNode)
    if findTermFormat(rootNode):
        tree[rootNode]['EnglishFormat'] = findTermFormat(rootNode)
    stack = [rootNode]
    store = []
    temp = []
    while stack:
        cur_node = stack[0]
        if store:
            print(store[-1])
            # cw.writerow(store[-1]+[sub(findNode(store[-1], tree)['documentation']), findNode(store[-1], tree)['EnglishFormat']]+ findWNSenseKey(store[-1][-1]))
            if findNode(store[-1], tree):
                if 'documentation' in findNode(store[-1], tree).keys():
                # if findNode(store[-1], tree)['documentation']:
                    if 'EnglishFormat' in findNode(store[-1], tree).keys():
                    # if findNode(store[-1], tree)['EnglishFormat']:
                        cw.writerow(store[-1]+[sub(findNode(store[-1], tree)['documentation']), findNode(store[-1], tree)['EnglishFormat']]+ findWNSenseKey(store[-1][-1]))
                    else:
                        cw.writerow(store[-1]+[sub(findNode(store[-1], tree)['documentation']), ['-']]+ findWNSenseKey(store[-1][-1]))
                elif 'EnglishFormat' in findNode(store[-1], tree).keys():
                    cw.writerow(store[-1]+[['-'], findNode(store[-1], tree)['EnglishFormat']]+ findWNSenseKey(store[-1][-1]))

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
        # print(store)
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
                curval = _finditem(tree,cur_node)
                if curval:
                    curval[child] = {}
                    # if findTelic(child):
                    #     curval[child]['Telic_Quale'] = findTelic(child)
                    # if findAgentive(child):
                    #     curval[child]['Agentive_Quale'] = findAgentive(child)
                    # if findConstitutive(child):
                    #     curval[child]['Constitutive_Quale'] = findConstitutive(child)
                    if findDocumentation(child):
                        curval[child]['documentation'] = findDocumentation(child)
                    if findTermFormat(cur_node):
                        curval[child]['EnglishFormat'] = findTermFormat(child)
                print(child)
    csv1.close()
    return

# CSVMAKE = make_csv()



def findStoreElement(node, storeList):
    # kp = []
    # while not kp:
    # kp = [v for v in storeList if v[-1] in findParents(node)]
        # for v in reversed(storeList):
        #     if v[-1] in findParents(node):
        #         kp.append(v)
    # med = [v for k,v in enumerate(storeList) if v[-1] in findParents(node)][0]
    # return [v for v in storeList if v[-1] in findParents(node)][0]
    return [v for v in storeList if v[-1] in findParents(node)]




def storageCleanup(storeList):
    import copy
    a = storeList
    b = copy.deepcopy(storeList)
    for i, j in enumerate(b):
        allChildrenGone = True
        for k in findChildren(j[-1]):
            if j + [k] not in b:
                allChildrenGone = False
        if allChildrenGone:
            a.remove(j)
        # remove the terminal nodes from store, cause we don't need them here
        if j and not findChildren(j[-1]):
            try:
                a.remove(j)
            except ValueError:
                pass
    # keep = [i for i in storeList if findChildren(i[-1])]
    return a



def make_csv_SUMO():
    import csv
    csv1 = open('SUMOcsv-test17.csv', 'w')
    cw = csv.writer(csv1, delimiter = ',', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    tree = {}
    nodes = []
    rootNode = 'Entity'
    tree[rootNode] = {'documentation': findDocumentation(rootNode)}
    if findTermFormat(rootNode):
        tree[rootNode]['EnglishFormat'] = findTermFormat(rootNode)
    stack = [rootNode]
    store = []
    temp = []
    # import copy
    while stack:
        # if len(nodes) % 10 == 0:
        #     print(len(store))
        #     s0 = copy.deepcopy(store)
        #     store = storageCleanup(store)
        #     print([x for x in s0 if x not in store])
        #     print(len(store))
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(cur_node)
        print(len(nodes))
        # xx = len(store)
        cleanUp = []
        if temp:
            # if store[-1][-1] in findParents(cur_node):
            #     temp = store[-1] + [cur_node]
            #     store.append(temp)
            # else:
            delta = 0

            for f in findStoreElement(cur_node, store):
                temp = f + [cur_node]
                if temp not in store:
                    store.append(temp)
                    delta += 1
                    if len(findParents(cur_node)) == 1 and not findChildren(cur_node):
                        cleanUp.append(temp)

                # print(store[-1])
        else:
            temp.append(cur_node)
            store.append(temp)
        # print(store)

        # here we add all the children of the current node, along with the doc and Eng of the children
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
                curval = _finditem(tree,cur_node)
                if curval:
                    curval[child] = {}
                    if findDocumentation(child):
                        curval[child]['documentation'] = findDocumentation(child)
                    if findTermFormat(cur_node):
                        curval[child]['EnglishFormat'] = findTermFormat(child)
                print(child)
        # here, we write the IS-A list for each entity, plus its doc and Eng, plus all its WN sense keys
        # findChildren(cur_node)[0] in stack
        if store:
            # delta = len(findStoreElement(cur_node, store))
            if delta == 1:
                print(store[-1])
                # replaced _finditem(tree,cur_node)   for   findNode(store[-1], tree)
                if _finditem(tree,cur_node):
                    if 'documentation' in _finditem(tree,cur_node).keys():
                        print(_finditem(tree,cur_node)['documentation'])
                        if 'EnglishFormat' in _finditem(tree,cur_node):
                            print(_finditem(tree,cur_node)['EnglishFormat'])
                            cw.writerow(store[-1]+[sub(_finditem(tree,cur_node)['documentation']), _finditem(tree,cur_node)['EnglishFormat']]+ findWNSenseKey(store[-1][-1]))
                        else:
                            cw.writerow(store[-1]+[sub(_finditem(tree,cur_node)['documentation'])]+ findWNSenseKey(store[-1][-1]))
                    elif 'EnglishFormat' in _finditem(tree,cur_node):
                        print(_finditem(tree,cur_node)['EnglishFormat'])
                        cw.writerow(store[-1]+[sub(_finditem(tree,cur_node)['EnglishFormat'])]+ findWNSenseKey(store[-1][-1]))
            else:
                for dy in range(1, (delta + 1)):
                # for dy in range(1, (len(store) - xx + 1)):
                    print(store[-dy])
                    if _finditem(tree, cur_node):
                        if 'documentation' in _finditem(tree,cur_node).keys():
                            print(_finditem(tree,cur_node)['documentation'])
                            if 'EnglishFormat' in _finditem(tree,cur_node):
                                print(_finditem(tree,cur_node)['EnglishFormat'])
                                cw.writerow(store[-dy]+[sub(_finditem(tree,cur_node)['documentation']), _finditem(tree,cur_node)['EnglishFormat']]+ findWNSenseKey(store[-dy][-1]))
                            else:
                                cw.writerow(store[-dy]+[sub(_finditem(tree,cur_node)['documentation'])]+ findWNSenseKey(store[-dy][-1]))
                        elif 'EnglishFormat' in _finditem(tree,cur_node):
                            print(_finditem(tree,cur_node)['EnglishFormat'])
                            cw.writerow(store[-dy]+[sub(_finditem(tree,cur_node)['EnglishFormat'])]+ findWNSenseKey(store[-dy][-1]))

        if len(store[-1]) == 4:
            m = [x for x in store if len(x) == 2 or len(x) == 1]
            cleanUp += m

        if cleanUp:
            for i in cleanUp:
                print('REMOVED FROM STORE: '),
                print(i)
                store.remove(i)




    csv1.close()
    return


def lastElementWidthPhrase(storeList):
    if len(storeList) > 3:
        lenlist = [len(x) for x in storeList]
        from itertools import groupby
        return [len(list(group)) for key, group in groupby(lenlist)][-1]


def storageCleanup2(storeList):
    import copy
    a = storeList
    b = copy.deepcopy(storeList)
    for i, j in enumerate(b):
        allChildrenGone = True
        for k in findChildren(j[-1]):
            if j + [k] not in b:
                allChildrenGone = False
        if allChildrenGone:
            a.remove(j)
        # remove the terminal nodes from store, cause we don't need them here
        # if j and not findChildren(j[-1]):
        #     try:
        #         a.remove(j)
        #     except ValueError:
        #         pass
    # keep = [i for i in storeList if findChildren(i[-1])]
    return a

tm = []
def findPath(node):
    # tm.append([node])
    t = [[node]]
    pr = findParents(node)
    if pr:
        t = [x + [y] for x in t for y in pr]
        for i in t:
            tm.append(i)
            node = i[-1]
            findPath(node)
    return tm

print(tm)

tm = []
def RealPath(node):
    # tm = []
    tm = findPath(node)
    if len(tm) == 0:
        return [[node]]
    elif len(tm) == 1:
        return [tm[0][::-1]]
    elif len(tm) > 1:
        tm2 = [x[1] for x in tm]

        # if len(tm2) > 1:
        from itertools import groupby
        m = [list(v) for k, v in groupby(tm2, lambda s: s == 'Entity')]
        if m[-1] != ['Entity']:
            m.pop()
        m = [m[n] + m[n+1] for n in range(len(m)) if n%2==0]
        m = [x for x in m if x[0] in findParents(node)]
        m = [x[::-1] for x in m]
        m = [x + [node] for x in m]
        return m


def make_csv_SUMO_ISA():
    import csv, time
    start_time = time.time()
    csv1 = open('SUMOcsvISA-test16.csv', 'w')
    cw = csv.writer(csv1, delimiter = ',', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    tree = {}
    nodes = []
    rootNode = 'Entity'
    tree[rootNode] = []
    stack = [rootNode]
    # store = []
    while stack:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(cur_node)
        print(len(nodes))
        if not tree[cur_node]:
            tm = []
            m = RealPath(cur_node)
            for i in m:
                # if i not in store:
                print(i)
                # store.append(i)
                tree[cur_node].append(i)
                cw.writerow(i)
            if findChildren(cur_node):
                for child in findChildren(cur_node):
                    if child not in tree.keys():
                        stack.append(child)
                        tree[child] = []
                    # print(child)
            print(time.time() - start_time)
    csv1.close()
    return

def SUMOISA():
    import csv
    csv1 = open('SUMOcsvISA-test17.csv', 'w')
    cw = csv.writer(csv1, delimiter = ',', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    for k,v in tree.items():
        for j in v:
            cw.writerow(j)
    csv1.close()
    return

# treekep in Console






def make_csv_SUMO_doc():
    import csv
    csv2 = open('SUMOcsvDoc-test8.csv', 'w')
    cwd = csv.writer(csv2, delimiter = ',', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    tree = {}
    nodes = []
    rootNode = 'Entity'
    tree[rootNode] = {}
    stack = [rootNode]
    while stack:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(cur_node)
        print(len(nodes))
        # here we add all the children of the current node to the tree
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
        if findDocumentation(cur_node):
            cwd.writerow([cur_node]+[findDocumentation(cur_node)])
        else:
            cwd.writerow([cur_node]+['-'])

    csv2.close()
    return


def make_csv_SUMO_WNSK():
    import csv
    csv2 = open('SUMOcsvWNSK-test5.csv', 'w')
    cwd = csv.writer(csv2, delimiter = ',', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    tree = {}
    nodes = []
    rootNode = 'Entity'
    # tree[rootNode] = findWNSenseKey(rootNode)
    # cwd.writerow([rootNode]+tree[rootNode])
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

        if cur_node not in tree.keys() and cur_node != 'Entity':

            WN = findWNSenseKey(cur_node)
            if WN:
                print(WN)
                tree[cur_node] = WN
                for i in WN:
                    cwd.writerow([cur_node]+[i])
                # this will write each sense key in one cell
                # cwd.writerow([cur_node]+tree[cur_node])
                # this will write all sense keys in one cell --- or not...
                # cwd.writerow([cur_node]+[findWNSenseKey(cur_node)])
            else:
                cwd.writerow([cur_node]+['-'])
        elif cur_node == 'Entity':
            tree[rootNode] = findWNSenseKey(rootNode)
            print(tree[rootNode])
            cwd.writerow([rootNode]+tree[rootNode])


    csv2.close()
    return


# from QualiaExtraction import findAgentive, findTelic, findConstitutive, findTelicAgentive
from QualiaExtraction import *
def makeSUMOQualiacsv():
    import csv
    csv2 = open('SUMOcsvQualia-test2.csv', 'w')
    cwd = csv.writer(csv2, delimiter = ',', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    tree = {}
    nodes = []
    rootNode = 'Entity'
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

        if cur_node not in tree.keys() and cur_node != rootNode:
            # if max([len(x) for x in treekeep[cur_node]]) > 3:

            Telic = findTelic(cur_node)
            # print('Telic Found!')
            Agentive = findAgentive(cur_node)
            # print('Agentive Found!')
            Constitutive = findConstitutive(cur_node)
            # print('Constitutive Found!')
            tree[cur_node] = {'Agentive':[], 'Telic': [], 'Constitutive': []}
            tree[cur_node]['Agentive'] = Agentive
            tree[cur_node]['Telic'] = Telic
            tree[cur_node]['Constitutive'] = Constitutive
            if tree[cur_node]:
                row = [cur_node]
                if tree[cur_node]['Agentive']:
                    row += tree[cur_node]['Agentive']
                else:
                    row += ['-']
                if tree[cur_node]['Telic']:
                    row += tree[cur_node]['Telic']
                else:
                    row += ['-']
                if tree[cur_node]['Constitutive']:
                    row += tree[cur_node]['Constitutive']
                else:
                    row += ['-']
                # print(tree[cur_node])
                cwd.writerow(row)
                # print(tree[cur_node])
        elif cur_node == 'Entity':
            tree[rootNode] = {'Agentive':findAgentive(rootNode), 'Telic': findTelic(rootNode), 'Constitutive': findConstitutive(rootNode)}
            # print(tree[rootNode])
            row = [rootNode]
            if tree[rootNode]['Agentive']:
                row += tree[rootNode]['Agentive']
            else:
                row += ['-']
            if tree[rootNode]['Telic']:
                row += tree[rootNode]['Telic']
            else:
                row += ['-']
            if tree[rootNode]['Constitutive']:
                row += tree[rootNode]['Constitutive']
            else:
                row += ['-']

            cwd.writerow(row)

    csv2.close()
    return


qualiadictionary = qualia
def qualiaWriteCSV(qualiadictionary):
    import csv
    csv2 = open('SUMOcsvQualia-test90.csv', 'w')
    cwd = csv.writer(csv2, delimiter = '|', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    done = []
    nodes = []
    rootNode = 'Entity'
    stack = [rootNode]
    while stack:
        print(len(done))
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(cur_node)
        print(len(nodes))

        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
        if cur_node != 'Entity' and cur_node not in done and cur_node in qualiadictionary.keys():
            QR = qualiadictionary[cur_node]
            if QR:
                for k,v in QR.items():
                    if k != 'typicalEventAgent' and k!= 'typicalActs':
                        if v and type(v) == list:
                            for j in v:
                                cwd.writerow([cur_node]+[k]+[j])
                        elif v and type(v) == str:
                            cwd.writerow([cur_node]+[k]+[v])
                        else:
                            cwd.writerow([cur_node]+[k]+['-'])
                done.append(cur_node)
            else:
                cwd.writerow([cur_node]+['-'])
        elif cur_node == 'Entity':
            for k, v in qualiadictionary[rootNode].items():
                cwd.writerow([rootNode]+[k]+['-'])
    csv2.close()
    return