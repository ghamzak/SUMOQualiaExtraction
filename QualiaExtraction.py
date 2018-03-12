__author__ = 'ghamzak'

##############################################################################
#                                                                            #
# Purpose: Extracting Qualia using the semantic predicates (via RE),         #
# and using documentation for possibly finding formal quale (via RE and WN). #
#                                                                            #
# Hints to Telic:                                                            #
# hasPurpose, instrument                                                     #
#  (instrument PurposeEvent Object) ,                                        #
# e.g.  (instrument ?ATTACH ?A) where A = Anchor                             #
# for transitive events, if patient is specific/not underspecified,          #
# it comes in the next line.                                                 #
#                                                                            #
# *** instrument could be a hint to Agentive quale too in case of            #
# intransitive events.                                                       #
#   e.g. Tooth: {Telic: Chewing}; Chewing: {Agentive: Tooth}                 #
#                                                                            #
# Hints to Agentive:                                                         #
# instrument, result                                                         #
#                                                                            #
# Hints to Constitutive:                                                     #
# part, initialPart, initiallyContainsPart, partTypes, typicalPart,          #
# typicallyContainsPart, component, member                                   #
# ** collect all the part-whole relationships, assign parts to wholes as     #
# Constitutive Quale                                                         #
#                                                                            #
# Hints to Formal:                                                           #
# Documentation: Adj.                                                        #
# ?SHAPE                                                                     #
# (attribute ?FOOD Liquid) : Drinking                                        #
# (attribute ?FOOD Solid) : Eating                                           #
# Artifact: {"is the product of a Making." : Agentive: Making}               #
# > Furniture: {"free-standing and movable (Adj.)                            #
# Artifact" ==> Formal: movable, "designed to rest on the Floor of a Room."  #
#  ==> Located(x,Floor)}                                                     #
# > Table: {"with four legs and a flat top." ==> Formal:  four legs          #
# and a flat top, "It is used either for eating, paperwork or meetings."     #
# ==> Telic: eating, paperwork or meetings.}                                 #
# > Desk: {"intended to be used for paperwork" ==> Telic: paperwork}         #
#                                                                            #
##############################################################################

import re, json
# from findRelations import retainUsefulBlocks, uncommentAndListAll, retainUsefulBlocksTerm
from SUMOjson import _finditem, findTermFormat
# from nltk.corpus import wordnet as wn
import nltk
from SUMOjson import findDocumentation
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from SUMOjson import see3

wordnet_lemmatizer = WordNetLemmatizer()

ipath = 'SUMOtxt/*'
all = see3
# entities = [re.findall(r'(?<=\(documentation ).+(?= English)', x)[0] for x in uncommentAndListAll(ipath) if re.findall(r'(?<=\(documentation ).+(?= English)', x)]

# note: for semantic predicates, you need blocks, not lines
# note2: fortunately, what uncommentAndListAll returns is exactly what we need


def findAllOccurrences(node):
    listed = [i for i in all if re.search(node, i)]
    return listed

# make sure we're limited to nouns:
def entityEnsure(node):
    if findTermFormat(node):
        word = findTermFormat(node)
    else:
        word = node.lower()
    pos = nltk.pos_tag(nltk.word_tokenize(word))
    judge = []
    if pos[-1][1] == 'NN':
        for i in pos[:-1]:
            if re.match(r'^VBG', i[1]) or re.match(r'VBN', i[1]):
                judge.append(True)
            elif re.match(r'^V', i[1]):
                judge.append(False)
            if i[1] == 'JJ':
                judge.append(True)
            if i[1] == 'NN':
                judge.append(True)
    if False in judge:
        return False
    else:
        return True


####### Capturing the Relations in SUMO #######
### Takes form Relation under Abstract
### they should all start with a small letter, as opposed to Processes which are capitalized

def findDomain(node):
    domains = [x for x in findAllOccurrences(node) if re.match(r'\(domain\w*? '+node+r' ', x)]
    domainfinal = []
    if domains:
        for j in domains:
            domainfinal.append((re.split(r' ', j)[2], re.sub(r'\)', r'', re.split(r' ', j)[3])))
    return domainfinal

def findRelationInstances(node):
    instances = [x for x in findAllOccurrences(node) if re.match(r'\(instance ', x) and re.search(node+r'\)$',x)]
    instancefinal = []
    if instances:
        for j in instances:
            instancefinal.append(re.split(r' ', j)[1])
    return instancefinal

def usefulRelations(): return [findRelationInstances('CaseRole')]

def SUMOrelationHierarchy():
    relations = {}
    nodes = []
    rootNode = 'Relation'
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
        if findSubrelations(cur_node):
            for sr in findSubrelations(cur_node):
                stack.append(sr)

        if cur_node not in relations.keys() and cur_node != 'Relation':
            relations[cur_node] = findRelationInstances(cur_node)
            print(findRelationInstances(cur_node))

        elif cur_node == 'Relation':
            relations[rootNode] = findRelationInstances(rootNode)
            print(relations[rootNode])

    return relations

def SentenceSegmentize(text):
    from nltk.tokenize import sent_tokenize
    return sent_tokenize(text)

def findBlock(node):
    if entityEnsure(node):
        pattern1 = r'\(documentation ' + node + r' EnglishLanguage\s*'
        # pattern2 = r'\(=>\s+\(instance.+' + node + r'\)'
        block = {}
        # if findDocumentation(node):
        block['doc'] = findDocumentation(node)
        block['semantics'] = [re.sub(r'\t', r' ', i) for i in findAllOccurrences(node) if re.search(r'\s+\(instance .+ ' + node + r'\)', i)]
        return block
    else:
        return {}

def arguments(semanticblock):
    # varnodes = []

    var2node = {}
    node2var = {}


    allvars = []
    splitted = re.split(r'\s+\(', semanticblock)
    for ind, x in enumerate(splitted):
        if len(re.split(r' ', x)) > 1 and re.search(r'\?', x):
            for j in re.split(r' ', x):
                if re.match(r'\?', j):
                    j = re.sub(r'\)+', r'', j)
                    if j not in allvars:
                        allvars.append(j)

    for i in splitted:
        if len(re.split(r' ', i)) == 3:
            for j in allvars:
                j0 = re.sub(r'\?', r'', j)
                j0 = r'\?' + j0
                if re.match(r'instance ', i) and re.search(j0 + r' ', i) and not re.match(r'\?', re.sub(r'\)', r'', re.split(r' ', i)[2])):
                    var2node[j] = re.sub(r'\)', r'', re.split(r' ', i)[2])
                    node2var[re.sub(r'\)', r'', re.split(r' ', i)[2])] = j
                # elif re.match(r'\?', re.sub(r'\)', r'', re.split(r' ', i)[2])):

    # remainingVars = [x for x in allvars if x not in var2node.keys()]
    semblockrelations = [x for x in splitted if re.search(r'\?', x) and re.match(r'\w', x) and not re.match(r'instance ', x)]
    for i in semblockrelations:
        # print(i)
        i = re.sub(r'\)+', r'', i)
        i = re.sub(r'\s+', r' ', i)
        rel = re.split(r' ', i)[0]
        if not re.search(r'Fn$', rel) and rel in nonInstanceRels and rel not in ['part', 'havePartTypes', 'initialPart', 'initiallyContainsPart', 'partTypes', 'typicalPart', 'typicallyContainsPart', 'component', 'geneticSubstrateOfVirus', 'half', 'inString', 'interiorPart', 'member', 'most', 'pathInSystem', 'piece', 'properPart', 'quarter', 'subCollection', 'subString', 'superficialPart', 'third']:
            for k in range(len(re.split(r' ', i))):
                if re.match(r'\?', re.split(r' ', i)[k]) and re.split(r' ', i)[k] not in var2node.keys() and findDomain(rel):
                    for m,n in enumerate(findDomain(rel)):
                        if k-1 == m:
                            var2node[re.split(r' ', i)[k]] = findDomain(rel)[k-1][1]
                            node2var[findDomain(rel)[k-1][1]] = re.split(r' ', i)[k]

    return var2node, node2var


# # Hints to Constitutive:
# # part (DONE), initialPart (DONE), initiallyContainsPart (DONE), partTypes (DONE), typicalPart (DONE),
# # typicallyContainsPart (DONE), component (DONE), member
# # ** collect all the part-whole relationships, assign parts to wholes as
# # Constitutive Quale
def findSubrelations(node): return [re.split(r' ', x)[1] for x in findAllOccurrences(node) if re.match(r'\(subrelation ', x) and re.search(node + r'\)$', x)]


relations = SUMOrelationHierarchy()
rl = [x for x in relations.values() if x]
rlsum = [x for x in rl] + relations.keys()
rlsumsum = [y for x in rlsum for y in x]
relationset = list(set(rlsumsum))
nonInstanceRels = list(set(relationset) - set(['instance']))

def findTelicRelations():
    # those relations whose documentation has the word purpose in it
    purposelist = []
    for i in relationset:
        if findDocumentation(i):
            if re.search(r'purpose', findDocumentation(i)):
                purposelist.append(i)
            elif re.search(r' used', findDocumentation(i)):
                purposelist.append(i)
    return purposelist
purposelist = findTelicRelations()
approvedPurposeList = ['resource', 'involvedInEvent', 'controlled']



check01 = findSubrelations('patient')
check02 = findSubrelations('involvedInEvent')
check03 = [findSubrelations(x) for x in check02 if findSubrelations(x)]
check032 = [x for y in check03 for x in y if y]
check040 = [findSubrelations(x) for x in check032 if findSubrelations(x)]
check041 = [x for y in check040 for x in y if y]
allchecks = list(set(check01) | set(check02) | set(check032) | set(check041))
## these are both needed very much for the online interpretation of axioms, which is the next step


### Approach 2: sweep over SUMO and find all the telic that's there, all the agentive that's there, and all the constitutive that's there
# for each, create a dictionary where each node maps to a list
from SUMOjson import *
from nltk.tag.stanford import StanfordPOSTagger as POS_Tag
home = '/Users/ghamzak/Downloads/stanford-postagger-2017-06-09'
_path_to_model = home + '/models/english-bidirectional-distsim.tagger'
_path_to_jar = home + '/stanford-postagger.jar'
st = POS_Tag(_path_to_model, _path_to_jar)
#st.tag(['stay'])

def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

relsToBeChecked = [x for x in nonInstanceRels if x and not re.search(r'Fn$', x)]
# relsToBeChecked3 = [x for x in relsToBeChecked if st.tag([camel_case_split(x)[-1]]) and re.match(r'V', st.tag([camel_case_split(x)[-1]])[0][1])]
relsToBeChecked2 = []
count = 0
for x in relsToBeChecked:
    print(x)
    count += 1
    print(count)
    tag = st.tag([camel_case_split(x)[-1]])
    if tag:
        if re.match(r'V', tag[0][1]):
            relsToBeChecked2.append(x)
finalRels = list(set(allchecks) | set(relsToBeChecked2))

def findUnder(node):
    nodes = []
    rootNode = node
    stack = [rootNode]
    while stack:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        # print(cur_node)
        if len(nodes) % 50 == 0:
            print(node)
            print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
    return list(set(nodes))
avoidList = list(set(findUnder('Process')) | set(findUnder('Relation')) | set(findUnder('Proposition')) | set(findUnder('Attribute')) | set(findUnder('ProcessTask')))
# len(avoidList) = 1667

keepList = list(set(findUnder('Object')) | set(findUnder('ContentBearingPhysical')) | set(findUnder('Quantity')) | set(findUnder('SetOrClass')) | set(findUnder('FinancialAsset')) | set(findUnder('PhysicalSystem')) | set(findUnder('Model')) | set(findUnder('Graph')) | set(findUnder('GraphElement')))
# len(keepList) = ?

def writeFile(filename, toBeWrittenObject):
    with open(filename, 'w') as tf:
        for i in toBeWrittenObject:
            tf.write(i+'\n')

writeFile('avoidList.txt',avoidList)
writeFile('keepList.txt',keepList)
writeFile('finalRels.txt',finalRels)


def qualiaWriteCSV(csvfilename, qualiadictionary, keylist):
    import csv
    csv2 = open(csvfilename, 'w')
    cwd = csv.writer(csv2, delimiter = '|', escapechar=' ', quotechar='|', quoting=csv.QUOTE_NONE)
    writtenAlready = []
    for ky in keylist:
        if ky not in writtenAlready and ky in qualiadictionary.keys():
            QR = qualiadictionary[ky]
            if QR:
                for k,v in QR.items():
                    if k != 'typicalEventAgent' and k!= 'typicalActs':
                        if v and type(v) == list:
                            for j in v:
                                cwd.writerow([ky]+[k]+[j])
                        elif v and type(v) == str:
                            cwd.writerow([ky]+[k]+[v])
                        else:
                            cwd.writerow([ky]+[k]+['-'])
                writtenAlready.append(ky)
                print(ky)
                print(len(writtenAlready))
            else:
                cwd.writerow([ky]+['-'])


    # done = []
    # nodes = []
    # rootNode = 'Entity'
    # stack = [rootNode]
    # while stack:
    #     # print(len(done))
    #     cur_node = stack[0]
    #     stack = stack[1:]
    #     nodes.append(cur_node)
    #     print(cur_node)
    #     if findChildren(cur_node):
    #         for child in findChildren(cur_node):
    #             stack.append(child)
    #     if cur_node != 'Entity' and cur_node not in done and cur_node in qualiadictionary.keys():
    #         QR = qualiadictionary[cur_node]
    #         if QR:
    #             for k,v in QR.items():
    #                 if k != 'typicalEventAgent' and k!= 'typicalActs':
    #                     if v and type(v) == list:
    #                         for j in v:
    #                             cwd.writerow([cur_node]+[k]+[j])
    #                     elif v and type(v) == str:
    #                         cwd.writerow([cur_node]+[k]+[v])
    #                     else:
    #                         cwd.writerow([cur_node]+[k]+['-'])
    #             done.append(cur_node)
    #             print(cur_node)
    #             print(len(done))
    #         else:
    #             cwd.writerow([cur_node]+['-'])
    #     elif cur_node == 'Entity':
    #         for k, v in qualiadictionary[rootNode].items():
    #             cwd.writerow([rootNode]+[k]+['-'])
    csv2.close()
    return

#first 30
def initializeMyQualia():
    nodes = []
    rootNode = 'Entity'
    qualia = {}
    stack = [rootNode]
    qualia[rootNode] = {'Telic': [], 'Agentive': [], 'Constitutive': [], 'typicalActs': [], 'Formal': []}
    done = [rootNode]
    verytopstatus = True
    # while stack and len(qualia) < 600:
    telicCount = 0
    agentiveCount = 0
    constitutiveCount = 0
    formalCount = 0
    nodesWithAnyQuale = 0
    while stack and len(qualia) < 30:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        # print(cur_node)
        # if len(nodes) % 50 == 0:
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
        p = []
        n = cur_node
        if verytopstatus:
            while n:
                if n == 'Entity':
                    break
                else:
                    n = findParents(n)[0]
                    p.append(n)
        if p and len(p) < 3:
            qualia[cur_node] = {'Telic': [], 'Agentive': [], 'Constitutive': [], 'typicalActs': [], 'Formal': []}
            done.append(cur_node)
        elif cur_node not in qualia.keys() and cur_node != rootNode and cur_node not in avoidList and cur_node in keepList:
            verytopstatus = False
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
MyQualia = initializeMyQualia()
qualiaWriteCSV('MyQualia-first30Nodes-test2.csv', MyQualia[0], MyQualia[8])

# 30 - 100
def MyQualiaSecondRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 100:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
MyQualia2 = MyQualiaSecondRun(MyQualia)
qualiaWriteCSV('MyQualia-first300Nodes.csv', MyQualia2[0], MyQualia2[8])

# 101 - 300
def MyQualiaThirdRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 300:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
from copy import deepcopy
MyQualia2Kept = deepcopy(MyQualia2)
MyQualia3 = MyQualiaThirdRun(MyQualia2)
qualiaWriteCSV('MyQualia-first100Nodes-test3.csv', MyQualia3[0], MyQualia3[8])


# 300 - 500
def MyQualiaFourthRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 500:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
from copy import deepcopy
MyQualia3Kept = deepcopy(MyQualia3)
MyQualia4 = MyQualiaFourthRun(MyQualia3)
qualiaWriteCSV('MyQualia-first500Nodes.csv', MyQualia4[0], MyQualia4[8])


# 500 - 700
def MyQualiaFifthRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 700:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
from copy import deepcopy
MyQualia4Kept = deepcopy(MyQualia4)
MyQualia5 = MyQualiaFifthRun(MyQualia4)
qualiaWriteCSV('MyQualia-first700Nodes.csv', MyQualia5[0], MyQualia5[8])


# 700 - 900
def MyQualiaSixthRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 900:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
from copy import deepcopy
MyQualia5Kept = deepcopy(MyQualia5)
MyQualia6 = MyQualiaSixthRun(MyQualia5)
qualiaWriteCSV('MyQualia-first900Nodes.csv', MyQualia6[0], MyQualia6[8])


# 900 - 1100
def MyQualiaSeventhRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 1100:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
from copy import deepcopy
MyQualia6Kept = deepcopy(MyQualia6)
MyQualia7 = MyQualiaSeventhRun(MyQualia6)
qualiaWriteCSV('MyQualia-first1100Nodes.csv', MyQualia7[0], MyQualia7[8])


# 1100 - 1500
def MyQualiaEighthRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 1500:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
from copy import deepcopy
MyQualia7Kept = deepcopy(MyQualia7)
MyQualia8 = MyQualiaEighthRun(MyQualia7)
qualiaWriteCSV('MyQualia-first1500Nodes.csv', MyQualia8[0], MyQualia8[8])


# 1500 - 2000
def MyQualiaNinthRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 2000:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
from copy import deepcopy
MyQualia8Kept = deepcopy(MyQualia8)
MyQualia9 = MyQualiaNinthRun(MyQualia8)
qualiaWriteCSV('MyQualia-first2000Nodes.csv', MyQualia9[0], MyQualia9[8])


# 2000 - 2500
def MyQualiaTenthRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 2500:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
MyQualia9Kept = deepcopy(MyQualia9)
MyQualia10 = MyQualiaTenthRun(MyQualia9)
qualiaWriteCSV('MyQualia-first2500Nodes.csv', MyQualia10[0], MyQualia10[8])


# 2500 - 3000
def MyQualiaEleventhRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 3000:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
MyQualia10Kept = deepcopy(MyQualia10)
MyQualia11 = MyQualiaEleventhRun(MyQualia10)
qualiaWriteCSV('MyQualia-first3000Nodes.csv', MyQualia11[0], MyQualia11[8])

# 3000 - 3500
def MyQualiaTwelfthRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 3500:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
MyQualia11Kept = deepcopy(MyQualia11)
MyQualia12 = MyQualiaTwelfthRun(MyQualia11)
qualiaWriteCSV('MyQualia-first3500Nodes.csv', MyQualia12[0], MyQualia12[8])



# 3500 - final
def MyQualiaLastRun(qualiadictionary):
    nodes = qualiadictionary[1]
    qualia = qualiadictionary[0]
    stack = qualiadictionary[2]
    telicCount = qualiadictionary[3]
    agentiveCount = qualiadictionary[4]
    constitutiveCount = qualiadictionary[5]
    formalCount = qualiadictionary[6]
    nodesWithAnyQuale = qualiadictionary[7]
    done = qualiadictionary[8]
    while stack and len(qualia) < 4000:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)

        if cur_node not in qualia.keys() and cur_node not in avoidList and cur_node in keepList:
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                done.append(cur_node)
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                if telicset:
                    telicCount += 1
                if agentiveset:
                    agentiveCount += 1
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1
    return qualia, nodes, stack, telicCount, agentiveCount, constitutiveCount, formalCount, nodesWithAnyQuale, done
MyQualia12Kept = deepcopy(MyQualia12)
MyQualia13 = MyQualiaLastRun(MyQualia12)
qualiaWriteCSV('MyQualia-final.csv', MyQualia13[0], MyQualia13[8])



import pickle

def save_obj(obj, name):
    with open('obj/'+ name + '.pkl', 'wb+') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

save_obj(MyQualia4, "MyQualia4")
save_obj(MyQualia5, "MyQualia5")
save_obj(MyQualia6, "MyQualia6")
save_obj(MyQualia7, "MyQualia7")
save_obj(MyQualia8, "MyQualia8")
save_obj(MyQualia9, "MyQualia9")
save_obj(MyQualia10, "MyQualia10")
save_obj(MyQualia11, "MyQualia11")
save_obj(MyQualia12, "MyQualia12")
save_obj(MyQualia13, "MyQualia13")

def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


def EntityQualiaMap():
    nodes = []
    rootNode = 'Entity'
    qualia = {}
    stack = [rootNode]
    qualia[rootNode] = {'Telic': [], 'Agentive': [], 'Constitutive': [], 'typicalActs': [], 'Formal': []}
    verytopstatus = True
    # while stack and len(qualia) < 600:
    telicCount = 0
    agentiveCount = 0
    constitutiveCount = 0
    formalCount = 0
    nodesWithAnyQuale = 0

    while stack:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        # print(cur_node)
        # if len(nodes) % 50 == 0:
        print(len(nodes))
        if findChildren(cur_node):
            for child in findChildren(cur_node):
                stack.append(child)
        p = []
        n = cur_node
        if verytopstatus:
            while n:
                if n == 'Entity':
                    break
                else:
                    n = findParents(n)[0]
                    p.append(n)
        if p and len(p) < 3:
            qualia[cur_node] = {'Telic': [], 'Agentive': [], 'Constitutive': [], 'typicalActs': [], 'Formal': []}
            # print(qualia[cur_node])
        elif cur_node not in qualia.keys() and cur_node != rootNode and cur_node not in avoidList and cur_node in keepList:
            verytopstatus = False
            if findBlock(cur_node):
                telicset = []
                agentiveset = []
                constitutiveset = []
                typicalActs = []
                formalset = []
                if findBlock(cur_node)['semantics']:
                    for s in findBlock(cur_node)['semantics']:
                        if s:
                            vn = arguments(s)
                            var2node = vn[0]
                            node2var = vn[1]
                            # for 2-place predicates (or more)
                            if cur_node in node2var.keys() and len(node2var) > 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                instanceInitial = []
                                if re.search(r'and', sparts[1]) and re.match(r'instance ', sparts[2]) and re.search(myvar+r' ', sparts[2]) and re.search(cur_node, sparts[2]):
                                    instanceInitial.append(sparts[2])
                                elif re.match(r'instance ', sparts[1]) and re.search(myvar+r' ', sparts[1]) and re.search(cur_node, sparts[1]):
                                    instanceInitial.append(sparts[1])
                                securedBy = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'securedBy ', x) and re.search(myvar, x)]
                                if securedBy and s not in telicset:
                                    sb = re.split(r' ', securedBy[0])
                                    if len(sb) == 3:
                                        telicset.append(var2node[sb[1]] + r' ' + sb[0] + r' ' + var2node[sb[2]])
                                    else:
                                        telicset.append(s)

                                inst = [x for x in sparts if re.match(r'instrument ', x) and re.search(myvar+r'\)+', x)]
                                if inst and s not in telicset:
                                    medlist = []
                                    cleanedinst = re.sub(r'\)+', r'', inst[0])
                                    instsplit = re.split(r' ', cleanedinst)
                                    instrel = instsplit[1]
                                    instrel = re.sub(r'\?', r'', instrel)
                                    ptinst = [x for x in sparts if re.match(r'patient ', x) and re.search(instrel+r' ', x)]
                                    if ptinst:
                                        ptinstclean = re.sub(r'\)+', r'', ptinst[0])
                                        ptsplit = re.split(r' ', ptinstclean)
                                        telicset.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                        medlist.append(var2node[ptsplit[1]] + r' ' + var2node[ptsplit[2]])
                                    else:
                                        telicset.append(var2node[instsplit[1]])
                                        medlist.append(var2node[instsplit[1]])
                                    if not medlist:
                                        telicset.append(s)

                                hasPurpose = [x for x in sparts if re.match(r'hasPurpose ', x) and re.search(myvar, x)]
                                if hasPurpose and instanceInitial:
                                    telicset.append(s)
                                    # translating this is not trivial... cause purpose is a formula, usually complex

                                result = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)+', x)]
                                # instead of instanceInitial, a more effective way is to count the parantheses
                                # and block things together, like in logic. good example: StationaryArtifact
                                if result:
                                    medlistresult = []
                                    resultcleaned = re.sub(r'\)+', r'', result[0])
                                    if result and s not in agentiveset:
                                        # agentiveset.append(s)
                                        resultsplit = re.split(r' ', resultcleaned)
                                        agentiveset.append(var2node[resultsplit[1]])
                                        medlistresult.append(var2node[resultsplit[1]])
                                    if not medlistresult and s not in agentiveset:
                                        agentiveset.append(s)

                                # formal quale
                                # shape = [x for x in sparts if re.match(r'shape ', x) and re.search(myvar + r' ', x)]
                                # if shape and s not in formalset:
                                #     medlistshape = []
                                #     if len(re.split(r' ', shape[0])) == 3:
                                #         formalset.append(re.split(r' ', shape[0])[-1])
                                #         medlistshape.append(re.split(r' ', shape[0])[-1])
                                #     if not medlistshape:
                                #         formalset.append(s)
                                #
                                # if len(sparts) == 4 and re.match(r'\(exists \(', sparts[2]) and re.match(r'\(member ', sparts[3]) and re.search(myvar+r'\)+', sparts[3]):
                                #     formalset.append(s)
                                # if re.match(r'meetsSpatially ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in formalset:
                                #     formalset.append(s)

                                # containsInformation = [x for x in sparts if re.match(r'containsInformation ', x) and re.search(myvar+r' ', x)]
                                # if containsInformation:
                                #     formalset.append(s)

                                # Agentive quale
                                if len(node2var) == 2 and re.match('result ', sparts[-1]) and re.search(myvar+r'\)+', sparts[-1]) and s not in agentiveset:
                                    agentiveset.append(s)

                                result2 = [x for x in sparts if re.match(r'result ', x) and re.search(myvar+r'\)', x)]
                                e1 = [x for x in sparts if re.match(r'exists \(', x)]
                                if result2 and instanceInitial and e1:
                                    if sparts.index(instanceInitial[0]) < sparts.index(e1[0]):
                                        agentiveset.append(s)

                                # constitutiive quale
                                part = []
                                for x in sparts:
                                    if re.match(r'part ', x) and len(re.split(r' ', x)) == 3 and not re.search(r'\(', x) and re.sub(r'\)+$', r'', re.split(r' ', x)[2]) == node2var[cur_node]:
                                        if re.split(r' ', x)[1] in var2node.keys():
                                            part.append(var2node[re.split(r' ', x)[1]])

                                if part:
                                    for i in part:
                                        if i not in constitutiveset:
                                            constitutiveset.append(i)

                                systemPart = [x for x in sparts if re.match(r'systemPart ', x) and re.search(myvar+r'\)', x)]
                                if systemPart:
                                    for i in systemPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])
                                abstractPart = [x for x in sparts if re.match(r'abstractPart ', x) and re.search(myvar+r'\)', x)]
                                if abstractPart:
                                    for i in abstractPart:
                                        if len(re.split(r' ', i))>2:
                                            if re.split(r' ', i)[1] in var2node.keys():
                                                if constitutiveset.append(var2node[re.split(r' ', i)[1]]) not in constitutiveset:
                                                    constitutiveset.append(var2node[re.split(r' ', i)[1]])

                                # typical acts occurring to this entity
                                patientOf = [x for x in sparts if re.match(r'patient ', x) and re.search(myvar+r'\)', x)]
                                if patientOf and s not in typicalActs:
                                    typicalActs.append(s)
                                offers = [x for x in sparts if re.match(r'offers ', x) and re.search(myvar+r'\)', x)]
                                if offers and s not in typicalActs:
                                    typicalActs.append(s)
                                potentialRel = [x for x in sparts for i in finalRels if re.match(i, x) and re.search(myvar, x)]
                                if potentialRel and s not in typicalActs:
                                    typicalActs.append(s)

                            ####### for 1-place predicates: #######
                            if cur_node in node2var.keys() and len(node2var) == 1:
                                sparts = re.split(r'\s\s+\(', s)
                                myvar = re.sub(r'\?', r'', node2var[cur_node])
                                # telic quale for activities, possibly? like the fact that when an Agent does an IntentionalProcess, s/he has a purpose.
                                if re.search(r'\(FoodForFn ', s) and s not in telicset:
                                    medlistfood = []
                                    fedSent = [re.sub(r'\)+', r'', x) for x in sparts if re.search('FoodForFn ', x)]
                                    if fedSent:
                                        if re.search(r'\(', fedSent[0]):
                                            foodpred = [x for x in re.split(r'\(', fedSent[0]) if re.match(r'FoodForFn ', x)]
                                            foodpred = re.split(r' ', foodpred[0])
                                            if re.match(r'\?', foodpred[1]):
                                                if foodpred[1] in var2node.keys():
                                                    fedOne = var2node[foodpred[1]]
                                                else:
                                                    fedOne = findDomain('FoodForFn')[0][1]
                                            else:
                                                fedOne = foodpred[1]
                                        else:
                                            fedOne = re.split(r' ', fedSent[0])[1]

                                        telicset.append(cur_node+' contains nutrients for '+fedOne)
                                        medlistfood.append(cur_node+' contains nutrients for '+fedOne)
                                    if not medlistfood:
                                        telicset.append(s)

                                # formal quale
                                # shape1 = [re.sub(r'\)+', r'', x) for x in sparts if re.match(r'shape ', x) and re.search(myvar + r' ', x)]
                                # if shape1 and s not in formalset:
                                #     medlistshape1 = []
                                #     if len(re.split(r' ', shape1[0])) == 3:
                                #         formalset.append(re.split(r' ', shape1[0])[-1])
                                #         medlistshape1.append(re.split(r' ', shape1[0])[-1])
                                #     if not medlistshape1:
                                #         formalset.append(s)
                                #
                                # sides = [x for x in sparts if re.match(r'FrontFn ', x) or re.match(r'BackFn ', x) and re.search(myvar, x)]
                                # if sides and s not in formalset:
                                #     formalset.append(s)
                                #
                                # location = [x for x in sparts if re.match(r'located ', x) or re.match(r'InnerBoundaryFn ', x) or re.match(r'OuterBoundaryFn ', x) and re.search(myvar, x)]
                                # if location and s not in formalset:
                                #     formalset.append(s)

                if findBlock(cur_node)['doc']:
                    for i in SentenceSegmentize(findDocumentation(cur_node)):
                        if re.search(r' e\.g\.$', i):
                            i = re.sub(r' e\.g\.$', r'', i)
                        if re.findall('purpose is', i):
                            telicset.append(re.findall(r'(?<=purpose is ).+', i)[0])
                        elif re.findall(r' intended to ', i):
                            telicset.append(re.findall(r'(?<= intended to ).+', i)[0])
                        elif re.findall(r' desgined to ', i):
                            telicset.append(re.findall(r'(?<= designed to ).+', i)[0])
                        elif re.findall(r' used for ', i):
                            telicset.append(re.findall(r'(?<= used for ).+', i)[0])
                        elif re.findall(r' used to ', i):
                            telicset.append(re.findall(r'(?<= used to ).+', i)[0])
                        elif re.findall(r' capable of ', i):
                            telicset.append(re.findall(r'(?<= capable of ).+', i)[0])
                        elif re.findall(r'Device that ', i):
                            telicset.append(re.findall(r'(?<=Device that ).+', i)[0])
                        elif re.findall(r'Artifact that ', i):
                            telicset.append(re.findall(r'(?<=Artifact that ).+', i)[0])

                        # formal quale:
                        # elif re.search(r'Any [\&%\w]+ that is ', i):
                        #     formalset.append(re.findall(r'(?<= that is ).+', i)[0])

                    ##### CONSTITUTIVE #####
                    typicalPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicalPart ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(typicalPart .+ ' + cur_node + r'\)', x)]
                    partTypes = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(partTypes ', r'', x)) for x in findAllOccurrences(cur_node) if re.search(r'\(partTypes .+ ' + cur_node + r'\)', x)]
                    nodepositivelookahead = r'(?='+cur_node+r'\)' + ')'
                    initialPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initialPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initialPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initialPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    initiallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(initiallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(initiallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    typicallyContainsPart = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(typicallyContainsPart ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(typicallyContainsPart )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    component = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(component ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(component )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(component )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    member = [re.sub(r' '+cur_node+r'\)', r'', re.sub(r'\(member ', r'', x)) for x in findAllOccurrences(cur_node) if (re.findall(r'(?<=\(member )[^\?].+ ', x) and re.findall(re.findall(r'(?<=\(member )[^\?].+ ', x)[0]+nodepositivelookahead, x))]
                    constitutiveset2 = list(set([x for x in typicalPart + partTypes + initialPart + initiallyContainsPart + typicallyContainsPart + component + member]))
                    constitutiveset = list(set(constitutiveset))
                    for i in constitutiveset2:
                        if i not in constitutiveset:
                            constitutiveset.append(i)
                formalset = findParents(cur_node)
                qualia[cur_node] = {'Telic': list(set(telicset)), 'Agentive': list(set(agentiveset)), 'Constitutive': list(set(constitutiveset)), 'typicalActs': list(set(typicalActs)), 'Formal': list(set(formalset))}
                if telicset or agentiveset or constitutiveset or formalset:
                    nodesWithAnyQuale += 1
                    # print('# of found qualia: '),
                    # print(nodesWithAnyQuale)
                if telicset:
                    telicCount += 1
                    # print('# of found telic relations: '),
                    # print(telicCount)
                if agentiveset:
                    agentiveCount += 1
                    # print('# of found agentive relations: '),
                    # print(agentiveCount)
                if constitutiveset:
                    constitutiveCount += 1
                if formalset:
                    formalCount += 1

                # for q in qualia[cur_node].items():
                #     if q[1]:
                #         print(q[0]),
                #         print(': '),
                #         print(q[1])


    return qualia

qualiaDict = EntityQualiaMap()
### remember for Telics extracted from documentation, get rid of possible "e.g." and "i.e." at the end of the line
# check UnpoweredDevice


# in a new dictionary, keep only those not under Process, Relation, Proposition, Attribute, ProcessTask
# do extract those under Object, ContentBearingPhysical, Quantity, SetOrClass, FinancialAsset, PhysicalSystem, Model, Graph, GraphElement

# then, for typicalActs, find the relations ultimately used.
# we don't try to translate the axioms into human-readable words or phrases

# for telic and agentive qualia, do translate into human-readable phrases


InherQTestDict = load_obj("MyQualia13")

# inheritence support
from copy import deepcopy

InherQTestDictKept = deepcopy(InherQTestDict)
qualiaInheritance = InherQTestDict

# remains for after manual correction of at least the first 100 extracted qualia
for i in qualiaInheritance[8]:
    if qualiaInheritance[0][i]['Telic']:
        telicAdd = qualiaInheritance[0][i]['Telic']
    if qualiaInheritance[0][i]['Agentive']:
        agentiveAdd = qualiaInheritance[0][i]['Agentive']
    if findChildren(i) and telicAdd:
        for c in findChildren(i):
            for t in telicAdd:
                qualiaInheritance[0][c]['Telic'].append(t)
    if findChildren(i) and agentiveAdd:
        for c in findChildren(i):
            for a in agentiveAdd:
                qualiaInheritance[0][c]['Agentive'].append(a)


for k, v in qualiaInheritance[0].items():
    print(k)
    temp = []
    g = k
    while g != 'Entity' and findParents(g):
        temp.append(findParents(g)[0])
        for i in findParents(g):
            if i in qualiaInheritance[0].keys():
                if qualiaInheritance[0][i]['Telic']:
                    if qualiaInheritance[0][i]['Telic'] != v['Telic']:
                        if isinstance(qualiaInheritance[0][i]['Telic'], list):
                            for x in qualiaInheritance[0][i]['Telic']:
                                InherQTestDictKept[0][k]['Telic'].append(x)
                        else:
                            InherQTestDictKept[0][k]['Telic'].append(qualiaInheritance[0][i]['Telic'])
                if qualiaInheritance[0][i]['Agentive']:
                    if qualiaInheritance[0][i]['Agentive'] != v['Agentive']:
                        if isinstance(qualiaInheritance[0][i]['Agentive'], list):
                            for x in qualiaInheritance[0][i]['Agentive']:
                                InherQTestDictKept[0][k]['Agentive'].append(x)
                        else:
                            InherQTestDictKept[0][k]['Agentive'].append(qualiaInheritance[0][i]['Agentive'])


q2 = qualia.keys()[470:]
for k in q2:
    print(k)
    temp = []
    g = k
    while g != 'Entity' and findParents(g):
        temp.append(findParents(g)[0])
        g = findParents(g)[0]
    print(temp)
    parentsAll[k] = temp


finalTelicCount = telicCount
finalAgentiveCount = agentiveCount
finalConstitutiveCount = constitutiveCount
finalFormalCount = formalCount
finalNodesWithQualiaCount = nodesWithAnyQuale

for i, j in qualia.items():
    tempCount = 0
    for p in parentsAll[i]:
        if p in qualia.keys():
            if qualia[p]['Telic'] and qualia[p]['Telic'] not in qualiaInheritance[i]['Telic']:
                qualiaInheritance[i]['Telic'].append(qualia[p]['Telic'])
                finalTelicCount += 1
                tempCount += 1
            if qualia[p]['Agentive'] and qualia[p]['Agentive'] not in qualiaInheritance[i]['Agentive']:
                qualiaInheritance[i]['Agentive'].append(qualia[p]['Agentive'])
                finalAgentiveCount += 1
                tempCount += 1
            if qualia[p]['Constitutive'] and qualia[p]['Constitutive'] not in qualiaInheritance[i]['Constitutive']:
                qualiaInheritance[i]['Constitutive'].append(qualia[p]['Constitutive'])
                finalConstitutiveCount += 1
                tempCount += 1
            if qualia[p]['Formal'] and qualia[p]['Formal'] not in qualiaInheritance[i]['Formal']:
                qualiaInheritance[i]['Formal'].append(qualia[p]['Formal'])
                finalFormalCount += 1
                tempCount += 1
    if tempCount != 0:
        finalNodesWithQualiaCount += 1
    print(finalNodesWithQualiaCount)



def openjson(jsonfile):
    import json
    with open(jsonfile) as df:
        data = json.load(df)
    return data

MyTree = openjson('wholeSUMO-09-09-17.json')


### 1/7 tests ###
lastQualiaDict = qualiaInheritance
mynodes = lastQualiaDict[8]
def findParents(node):
    # note: a node may have an arbitrary number of parents
    # e.g. findParents('ContentBearingProcess') should return ['ContentBearingPhysical', 'Process']
    searchpattern = r'(?<=\(subclass )' + node + r' '
    parents = [re.sub(r'\)', r'', re.split(' ', x)[-1]) for x in see if re.search(searchpattern, x)]
    return parents

def makeISADict(nodes):
    ISA = {}
    for i in nodes:
        if i not in ISA.keys():
            ISA[i] = findParents(i)
    return ISA

def makeTelicDict(nodes):
    TD = {}
    for i in nodes:
        if i not in TD.keys() and i in lastQualiaDict[0].keys():
            TD[i] = lastQualiaDict[0][i]['Telic']
    return TD

def makeAgentiveDict(nodes):
    AD = {}
    for i in nodes:
        if i not in AD.keys() and i in lastQualiaDict[0].keys():
            AD[i] = lastQualiaDict[0][i]['Agentive']
    return AD

def makeConstitutiveDict(nodes):
    AD = {}
    for i in nodes:
        if i not in AD.keys() and i in lastQualiaDict[0].keys():
            AD[i] = lastQualiaDict[0][i]['Constitutive']
    return AD



with open('ISArelations.json', 'w') as out1:
    json.dump(makeISADict(mynodes), out1, sort_keys=False, ensure_ascii=True)

with open('TelicRelations.json', 'w') as out2:
    json.dump(makeTelicDict(mynodes), out2, sort_keys=False, ensure_ascii=True)

with open('AgentiveRelations.json', 'w') as out3:
    json.dump(makeAgentiveDict(mynodes), out3, sort_keys=False, ensure_ascii=True)

with open('ConstitutiveRelations.json', 'w') as out4:
    json.dump(makeConstitutiveDict(mynodes), out4, sort_keys=False, ensure_ascii=True)


# 1/9 tests to interpret hasPurpose predicate

# we need the functions arguments(semanticblock) and findDomain(node)
semanticblock = "(=> (instance ?X ExerciseCenter) (hasPurpose ?X (exists (?DEVICE) (and (or (instance ?DEVICE AerobicExerciseDevice) (instance ?DEVICE AnaerobicExerciseDevice)) (located ?DEVICE ?X)))))"
node = "PaintingDevice"
findDomain(node)
findDocumentation("BoatSeat")

with open('TelicRelations.json') as df1:
    dt = json.load(df1)

with open('AgentiveRelations.json') as df2:
    at = json.load(df2)

with open('ConstitutiveRelations.json') as df3:
    ct = json.load(df3)




"""
The following "extra long" block cleans up. Commented out for now.
"""


"""
save_obj(dt, "Telic0")
dt1 = deepcopy(dt)

dt1["ExerciseCenter"][0] = "has equipment and services for physical training and keeping fit"
dt1["WearableItem"][0] = "worn on the body"
dt1["Tomb"] = "contain someone who is &%Dead"
dt1["SurveillanceSystem"] = "provide security by recording sound or video in a certain location and showing it instantly to people, presumably a &%SecurityUnit"
dt1["TransferSwitch"][0] = "switches a load between two &%PowerSource"
del dt1["TransferSwitch"][1]
del dt1["AirConditioner"][0]
del dt1["AirConditioner"][0]
dt1["AirConditioner"][0] = "provide comfort during hot or cold weather by keeping the air in an area a specific temperature"
del dt1["FourWheelDriveVehicle"][0]
dt1["ElectronicDataStorageDevice"][0] = "storing data (information) in some encoding scheme designed to be interpreted by electronic devices."
del dt1["ToxicOrganism"]
dt1["BoatSeat"][0] = "provides Sitting for Human in WaterVehicle"
del dt1["MechanicalJoint"][0]
del dt1["AirConditioningCondenser"][0]
del dt1["AirConditioningCondenser"][0]
del dt1["AirConditioningCondenser"][0]
del dt1["KnockLight"][1]
del dt1["Solenoid"][1]
dt1["DisplayArtifact"][0] = "posting content so that it can be disseminated to the public"
del dt1["CommodoreWheel"]
del dt1["InteriorVehicleEquipment"]
del dt1["LandVehicle"][2]
del dt1["ElectronicLock"][0]
dt1["ResidentialBuilding"][0] = "provides some accomodation for sleeping"
del dt1["Sewage"]
dt1["JudicialOrganization"][0] = "render judgments according to the statutes or regulations of a government or other organization"
dt1["Wastebasket"][0] = "holds trash"
del dt1["Eye"]
del dt1["Broom"][2]
dt1["Tachometer"][0] = "&%Measuring the number of &%RevolutionsPerMinute of an object"
del dt1["Tachometer"][1]
dt1["WebPageModule"][0] = "Destination of DataTransfer from PageModuleServer"
del dt1["HairDryer"][1]
del dt1["VendingDevice"][1]
del dt1["VendingDevice"][1]
del dt1["OxygenSensor"][0]
del dt1["Organism"]
del dt1["Shield"][2]
dt1["PaintingDevice"] = "Painting"
del dt1["WashBasin"][1]
del dt1["WashBasin"][1]
dt1["Sofa"] = findDocumentation("Sofa")
del dt1["Distributor"][1]
del dt1["Planer"][1]
del dt1["Chain"]
dt1["Niqab"][0]= "worn to cover a woman's lower part of the face"
del dt1["ExhaustValve"]
del dt1["Human"]
del dt1["DramaticPlay"][0]
del dt1["M240"]
dt1["HotelFrontDesk"][0] = "&%CheckInService and &%CheckOutService transactions"
dt1["AutoAirbag"][0] = "detect a sudden &%Decelerating deploy the airbag by an explosive release of a &%Gas that fills the bag before the occupant can be thrown against the hard interior surfaces of the &%Vehicle."
del dt1["IntakeValve"]
dt1["MechanicalTap"] = ["Making Bolt"]
# del dt1["MechanicalTap"][1]
del dt1["MediaSystem"][0]
del dt1["MediaSystem"][0]
dt1["MediaSystem"][0] = "enable the &%RadiatingSound of &%AudioRecording and &%RadiatingLight of &%VideoRecording"
del dt1["FuelCapLock"][0]
dt1["FuelCapLock"][0] = "prevent &%Stealing the &%Fuel from the &%GasTank"

save_obj(dt1, "Telic1")

# dt2 = deepcopy(dt1)

dt2 = load_obj("Telic1")

del dt2["Database"]
del dt2["Tripod"]
dt2["ReferenceText"][0] = "not to be read from beginning to end, but which is meant to be consulted to answer specific factual questions"
del dt2["GreaseGun"][0]
del dt2["GreaseGun"][0]
del dt2["Button"][0]
del dt2["VehicleBrake"][0]
del dt2["VehicleBrake"][1]
dt2["Meal"][1] = "Eating"
del dt2["Earphone"][0]
del dt2["Earphone"][0]
dt2["Earphone"].append("RadiatingSound")
del dt2["UnpoweredDevice"]

save_obj(dt2, "Telic2")

dt3 = deepcopy(dt2)

dt3["Vehicle"][0] = "Transportation"
del dt3["CrudeOilPipeline"][0]
dt3["Furniture"][0] = "designed to rest on the &%Floor of a &%Room"
del dt3["FourByFourTire"]
dt3["BrakeShoe"][0] = "press against a rotating &%BrakeDrum to cause vehicle braking"
del dt3["Oven"][2]
del dt3["TaxReturn"][1]
del dt3["TaxReturn"][1]
dt3["AutomobileSeat"][0] = "lets Human be Sitting in Automobile"
del dt3["Pencil"]
dt3["Respirator"][1] = "protect the wearer from &%Injuring caused by &%Inhaling of harmful substances"
dt3["ManifoldHeatControlValve"][0] = "sends hot &%Exhaust gases to pre-heat the &%FuelVapor for more efficient &%Combustion"
del dt3["Rug"][1]
dt3["EntertainmentBuilding"] = "location of RecreationOrExercise"
dt3["Subway"][0] = "designed for running trains that move people"
dt3["Subway"].append("location of Human Transportation")
dt3["PictureFrame"][0] = "protecting and accenting the picture"
dt3["Tableware"][0] = "&%Ingesting (&%Eating and/or &%Drinking) a meal"
del dt3["Closet"][0]
del dt3["Aerator"][1]
dt3["Aerator"][1] = "Combining Air"
del dt3["SafetyHarness"][1]
dt3["SafetyHarness"][0] = "protect a person from &%Injuring"
dt3["RunningTrack"][0] = "a path for people running"
del dt3["WaterVehicle"][2]
dt3["Fireplace"][1] = "location of Combustion"
dt3["Chimney"][0] = "Removing Smoke"
del dt3["Chimney"][1]
dt3["Concrete"][0] = "building materials"
del dt3["EngineGovernor"][1]
del dt3["EngineGovernor"][1]
del dt3["SpeakerDevice"][1]
dt3["PortableComputer"][0] = "designed to be tranferred easily by a &%Human from one location to another"
del dt3["Spacecraft"][1]
dt3["Workshop"][0] = "Making Artifact"
dt3["GameGoal"][0] = "destination of GameShot to constitutue a Score"

save_obj(dt3, "Telic3")
dt4 = load_obj("Telic3")

dt4["BrakeCaliper"][0] = "presses a &%BrakePad against a &%BrakeRotor"
del dt4["BrakeCaliper"][1]
del dt4["BrakeCaliper"][2]
del dt4["Artifact"][1]
del dt4["ElectricDevice"][3]
del dt4["ElectricDevice"][2]
del dt4["ElectricDevice"][0]
dt4["ExhaustManifold"][0] = "take exhaust &%Gases from the &%Engine &%Cylinders and route them to the &%Muffler and &%Tailpipe"
del dt4["Gasket"][0]
del dt4["BathingDevice"][1]
dt4["Mine"][0] = "origin of Removing Mineral"
dt4["FireExtinguisher"][1] = "&%Stop small &%Fire which is possible for &%Human to carry"
del dt4["FireExtinguisher"][2]
del dt4["FireExtinguisher"][0]
del dt4["GovernmentCabinet"][0]
dt4["MechanicalDie"][0] = "creating a &%MechanicalNut out of a &%Rod"
del dt4["MechanicalDie"][1]
del dt4["CH53E"]
dt4["Restaurant"][0] = "selling Food to customers which is intended to be eaten on the premises"
del dt4["Wrench"][1]
del dt4["SwitchDevice"][0]
dt4["SportsGround"][0] = "location where Sports are played"
dt4["AirPump"][0] = "Transportation of Air"
del dt4["AirPump"][1]


save_obj(dt4, "Telic4")

dt5 = load_obj("Telic4")

del dt5["TelephoneCradle"]
dt5["Stairway"][0] = "allows one to climb, step by step, from one level to another"
del dt5["M3M"]
dt5["FishTank"][0] = "designed to hold &%Water and &%Fish"
dt5["SteeringBox"][0] = "transmits &%Motion to the &%SteeringArms"
del dt5["UnitOfAtmosphericPressure"]
del dt5["Device"][1:4]
del dt5["WheelChock"][1]
dt5["TVRemoteControl"][0] = "ElectronicSignalling to TelevisionReceiver"
dt5["CustomerSupport"][0] = "having its &%members be &%customerRepresentatives"
del dt5["Commission"][1]
dt5["HotelUnit"][0] = "a traveler sleeps in when he is in &%TravelerAccomodation"
dt5["DanceHall"][0] = "location of Dancing and MakingMusic"
del dt5["Handle"][0]
del dt5["GrecianTub"]

save_obj(dt5, "Telic5")

dt6 = load_obj("Telic5")

dt6["PictureFrame"][0] = "protecting and accenting the picture"
del dt6["Closet"][0]
del dt6["Aerator"][1]
del dt6["Aerator"][1]
dt6["SafetyHarness"][0] = "protect a person from &%Injuring"
del dt6["SafetyHarness"][1]
dt6["RunningTrack"][0] = "path where Human "

del dt6["WaterVehicle"][2]
del dt6["Fireplace"][1]
dt6["Chimney"][0] = "Removing Smoke"
del dt6["Chimney"][1]
dt6["Concrete"][0] = "used as building materials"
del dt6["EngineGovernor"][1]
del dt6["EngineGovernor"][1]
del dt6["SpeakerDevice"][1]

def del6(node, index):
    del dt6[node][index]
    return
def change6(node, index, value):
    dt6[node][index] = value
    return
def add6(node, value):
    dt6[node].append(value)
    return

del dt6["PortableComputer"]
del6("Spacecraft", 1)
change6("Workshop", 0, "Making Artifact")
del6("BathingDevice", 0)
del6("Application", 1)
del6("Handle", 0)
del dt6["GrecianTub"]
del6("AirConditioningEvaporator", 3)
del6("AirConditioningEvaporator", 1)
change6("ElectricalPlug", 0, "completelyFills ElectricalOutlet")
change6("Airline", 0, "serviceProvider of AirTransportationService")
del6("Monument", 2)
del6("Eyelid", 0)
del dt6["FanBelt"]
del6("Photocopier", 5)
del6("Photocopier", 2)
del6("Photocopier", 1)
change6("ExplosiveDevice", 2, "Explosion causing Damaging")
change6("Bandage", 0, "Covering as subProcess of TherapeuticProcess")
del6("Bandage", 1)
del6("RemoteIgnitionControl", 0)
add6("RestaurantBuilding", "where people pay to be served food and eat")
del6("RestaurantBuilding", 0)
change6("Campground", 0, "to have &%MobileResidences")
del6("Campground", 1)
change6("PlayArea", 0, "where RecreationOrExercise of HumanChild takes place")
del6("AudioRecorder", 2)
del6("AudioRecorder", 0)
del6("RoomHeater", 0)
del6("FuelPump", 2)
del6("FuelPump", 1)
del6("Garage", 0)
change6("Brick", 0, "Constructing")
change6("TrapOrCage", 0, "to trap or cage &%Animals")
del6("TrapOrCage", 1)
change6("ContraceptiveDevice", 0, "permit sexual intercourse but which reduce the likelihood of conception")
del dt6["RemoteKeylessSystem"]
del6("Weapon", 2)
change6("Bed", 0, "sleeping")
del6("Glue", 2)
del6("NonprofitOrganization", 1)

save_obj(dt6, "Telic_6")


dt7 = load_obj("Telic_6")
def del7(node, index):
    del dt7[node][index]
    return
def change7(node, index, value):
    dt7[node][index] = value
    return
def add7(node, value):
    dt7[node].append(value)
    return


change7("TapeRecorder", 0, "stores the recorded &%AudioRecording on a &%RecordingTape")
del7("TapeRecorder", 1)
change7("Modem", 0, "facilitate communication between computers")
change7("ElectricCoffeeMaker", 0, "Making Coffee")
del7("ElectricCoffeeMaker", 2)
del7("ElectricCoffeeMaker", 1)
add7("Kidney", "separates urine from other &%BodySubstances and passes it to the bladder")
del7("CoolingDevice", 1)
change7("Generator", 0, "Process resulting in Electricity")
del7("GrabBar", 1)
del7("Screwdriver", 1)
del7("VehicleController", 0)
del7("Veil", 1)
del7("Charger", 0)
del7("Towel", 2)
del7("Towel", 0)
change7("WaterPump", 0, "Transfer Water")
del7("WaterPump", 1)
change7("Hijab",0, "Woman wears it")
del7("Clock", 0)
change7("Key", 0, "opens and closes a &%Lock")
change7("SportsFacility", 0, "locating Sport events")
change7("VCRSystem", 0, "can play &%AudioRecording and &%VideoRecording that is stored in a &%VHS")
del7("Ballot", 1)
del7("HeatingDevice", 2)
change7("WireLine", 0, "conducting electricity")
del7("SwimmingPool", 0)
del7("Brake", 0)
change7("PlaceOfWorship", 0, "locating ReligiousProcess events")
del7("SafetyDevice", 1)
del7("SafetyDevice", 0)
change7("Freighter", 0, "Transportation of Object")
add7("Freighter", "transports &%Artifacts")
del dt7["VehicleRoofRack"]
add7("AntiArmorWeapon", "damage the armor of military vehicles or bunkers")
change7("Auditorium", 0, "locating Demonstrating events")
change7("BlisterAgent", 0, "Damaging Tissue")
del7("WritingDevice", 0)
del7("WritingDevice", 0)
del7("WebStore",0)
del7("WalkingCane", 0)
change7("SteeringColumnLock", 1, "protect an &%Automobile from &%Stealing")
del dt7["BusinessCenter"]

save_obj(dt7, "Telic_7")

dt7 = load_obj("Telic_7")

del7("Radiator", 2)
del7("GreaseFitting", 1)
change7("Bullet", 0, "Shooting")
del dt7["Harrier2"]
change7("AutomobileTransmission", 0, "allow a given rotational speed of the &%Crankshaft to be translated ultimately to different speeds of the &%Driveshaft")
del dt7["IntermittentCombustionEngine"]
change7("Sprinkler", 0, "loosely distributes a substance, either solid (e.g. Salt or herbs) or liquid (e.g. water sprinkler)")
change7("Apron", 0, "for wearing when Cooking")
change7("IroningBoard", 0, "used as a surface for Ironing")
change7("Elevator", 0, "moving people or objects from one floor to another in a building")
del7("Oar", 1)
change7("GasCompressor", 1, "Compressing Gas Object")
del7("GasCompressor", 0)
del7("WearingFrictionSurface", 1)
change7("Transitway", 0, "path for Transportation")
del7("MeasuringDevice", 2)
change7("Sidewalk", 0, "path for Walking")
del7("SparkPlug", 1)
del7("SparkPlug", 0)
change7("SentientAgent", 0, "capable of &%Perception and experiences some level of consciousness")
change7("Fodder", 0, "DomesticAnimal Eating it")
change7("KitchenArea", 0, "locating Cooking events")

del dt7["DamagedVehicle"]
change7("Lyrics", 0, "Singing")
del7("Lyrics", 1)
del7("Bidet", 1)
del7("MudTire", 0)
change7("PositiveCrankcaseVentilationValve", 0, "send unburned fuel that escapes into the &%Crankcase back to the &%CombustionChamber")
change7("AlarmClock", 0, "will radiate sound when a certain time is set")
change7("AudioCDSystem", 0, "plays &%AudioRecording")
del7("AudioCDSystem", 1)
del dt7["HumanLanguage"]

save_obj(dt7, "Telic_8")

# run findDocumentation, pickle, save_obj, load_obj, del7, change7, add7... Then load_obj(last object) and give it a name

dt7 = load_obj("Telic_8")

change7("VehicleSafetyDevice", 0, "is designed to prevent (or lessen the likelihood of) the &%Injuring of a &%Human while in &%Vehicle.")
del7("VehicleSafetyDevice", 1)
change7("Dish", 0, "&%Holder for &%Food")
del dt7["BabyMonitoringSystem"]
del7("AutomaticGun", 1)
change7("Bus", 0, "transport large numbers of passengers")
del7("Document", 3)
change7("Store", 0, "locating FinancialTransaction events")
change7("Nest", 0, "locating Birth events")
del7("Baton", 0)
add7("Manufacturer", "manufactures &%Products")
change7("Manufacturer", 0, "Manufacture")
del7("Pipeline", 0)
change7("DataWarehouse", 0, "containing  information about a particular subject &%inScopeOfInterest of a particular &%Agent")
del7("DataWarehouse", 1)
change7("TDDPhone", 0, "Telephoning for Deaf Agent")
del7("TDDPhone", 1)
change7("Detergent", 1, "Removing Substance from surface of OBJECT")
del dt7["OutboardEngine"]
del7("StarterMotor", 0)
del dt7["InternalCombustionEngine"]
del7("CatalyticConverter", 0)
del dt7["HydraulicFluid"]
del7("Wallpaper", 1)
change7("Tube", 1, "Transfer Fluid")
del7("AH1", 1)
del dt7["CarAlarm"]
change7("EngineFan", 1, "Cooling the engine")
del7("EngineFan", 0)
del dt7["Copper"]
change7("ComputerDisk", 0, "read while being spun in a &%DiskDrive")
del7("PaperShredder", 1)
del7("TwoWheelDriveVehicle", 1)
del dt7["OutletAdapter"]
del7("WindowCovering", 1)
change7("Electrolyte", 0, "conducts &%Electricity")
del dt7["Animal"]
del7("TransportationDevice", 3)
del7("TransportationDevice", 1)
del7("TransportationDevice", 0)

save_obj(dt7, "Telic_9")





dt7 = load_obj("Telic_9")

change7("BrakePedal", 0, "destination of Pushing")
del7("BrakePedal", 1)
add7("BrakePedal","being pushed to activate the bakes of the vehicle")
change7("GameBoard", 0, "location of Game events")
change7("Easel", 0, "destination of Putting Flat Artifact")
del7("Sonar", 1)
del7("ParkingBrake", 1)
change7("Valve", 1, "regulates, directs or controls the Flow of a Fluid")
del7("Valve", 2)
del7("Microwave", 2)
del7("Microwave", 0)
change7("Hammock", 0, "location of LyingDown events")
change7("Misbahah", 0, "Muslim Praying")
del7("HeatSealer", 1)
del7("BedLinen", 2)
del7("BedLinen", 0)
change7("Seat", 0, "location of Sitting Human")
del7("Seat", 1)

change7("Holster", 0, "contains Pistol")
change7("Reel", 0, "Keeping LongAndThin and Pliable CorpuscularObject")
del7("Reel", 1)
change7("EngineWaterPump", 0, "move Water")
del7("PotOrPan", 2)
del7("PotOrPan", 1)
del7("GasPedal", 1)
change7("GasPedal", 0, "controls the flow of &%Fuel")
change7("Driveshaft", 0, "transmits power from the &%AutomobileTransmission to a &%Differential or more directly to the &%Wheels of an &%Automobile")

del7("AnimalController",0)
change7("AmphibiousReconnaissanceUnit", 0, "agent of AmphibiousReconnaissance")
change7("Bag", 0, "contains and Transfer Object")
del7("Bag", 1)

del7("CleaningDevice", 2)
change7("Battalion", 0, "independent operations")
change7("Warehouse", 0, "location of Keeping Product")
del dt7["AnimalLanguage"]
change7("Hinge", 0, "connects two Objects and enables either Object1 or Object2 to do Rotating")
del7("Aircraft", 2)
change7("Whiteboard", 0, "Writing on")
change7("Barricade", 0, "block Translocation")
add7("Barricade", "impede the advance of an enemy")
del7("BrakeSystem", 0)
change7("Road", 0, "location of Transportation with LandVehicle")
del7("HearingProtection", 1)
del7("HearingProtection", 0)
del7("Hand", 0)
change7("BusStop", 0, "location of Boarding and Deboarding a Bus")
change7("MolotovCocktail", 0, "Combustion and Damaging an Entity")
del7("MolotovCocktail", 2)
change7("Waterway", 0, "path for WaterTransportation")
change7("OilPan", 0, "contains Oil")
del7("DVDSystem", 1)
change7("DVDSystem", 0, "play the contents of &%VideoRecording and &%AudioRecording stored in a &%DVD")
change7("BrushOrComb", 0, "Removing or SurfaceChange")
del7("BrushOrComb", 1)
change7("DressingRoom", 0, "location of ChangingClothing")
change7("AirAttackMissile", 1, "Damaging Entity in AtmosphericRegion")
change7("AirTransitway", 0, "path for Transportation")


del7("Toothbrush", 0)
change7("String", 0, "Tying things together")
change7("Nutrient", 0, "contains nutrients for Organism")
change7("PlantRoot", 0, "to absorb nutrients from the ground and to anchor the &%Plant in place")
del dt7["FourStrokeEngine"]
change7("Jilbab", 0, "Woman wears it")
change7("Park", 0, "location of RecreationOrExercise")
del dt7["VacuumHose"]
change7("AnimalResidence", 0, "Animal not Human inhabits it")
del7("Fighter", 1)
del7("Telex", 0)
change7("ArtWork", 0, "Perception by Human")
del7("ArtWork", 1)
change7("TireChain", 0, "covers Wheel of a RoadVehicle and causes Friction")
del7("EngineCoolingSystem", 0)
del dt7["Oqal"]


change7("Blanket", 1, "Heating Human in Bed")
del7("ElectricalOutlet", 1)
change7("Casino", 1, "location of Game involving Betting")
change7("Drill",1, "Cutting and creating a Hole")
del7("Drill", 2)
del7("MusicalInstrument", 0)
change7("Flywheel", 0, "smooth the application of force or keep a &%Shaft spinning in the absence of other power inputs")
del7("Stove", 1)
change7("Mattress", 0, "Human sleeps On it")
change7("VehicleSeat", 0, "location of Sitting Human in Vehicle")
change7("GasTank", 0, "contains Fuel")
del7("GasTank", 2)
change7("Coffin", 0, "location of HumanCorpse")
change7("GameRoom", 0, "location of Game")
change7("PressureControlValve", 0, "controls the pressure in a fluid")


del7("FileDevice", 0)
del dt7["OakWood"]
change7("Lathe", 0, "SurfaceChange or ShapeChange Entity")
del7("Lathe", 2)
del7("Lathe", 1)
change7("IndustrialPlant", 0, "location of Manufacture")
del dt7["Air"]
del dt7["BrakePad"]
change7("Dishdashah", 0, "Man wears it")
del dt7["Grasshopper"]
change7("Crib", 0, "location of Asleep HumanBaby")

save_obj(dt7, "Telic_91")

change7("Classroom", 0, "location of EducationalProcess")
change7("Holder", 0, "to hold something else")
del dt7["Substance"]
change7("PrayerMat", 0, "Praying On it")
del dt7["Rod"]
del7("OpticalDevice", 1)
del7("WashingDevice", 1)
del7("BeamRidingGMissile", 1)
del dt7["M197GatlingGun"]
change7("Filter", 0, "Removing from Mixture")
del7("Filter", 1)
del7("InfraRedGMissile", 1)
change7("ProtectiveEyewear", 0, "prevent the &%Injuring of &%Eye of the wearer")
del dt7["Tailpipe"]
change7("Shower", 0, "WaterMotion from it")
add7("Shower", "sprays water over you")
del dt7["EngineControlModule"]
change7("AirFilter", 0, "Removing Solid from Air Mixture")
del7("AirFilter", 1)
add7("AirFilter", "remove &%Solid impurities from &%Air")
del7("Radar", 1)
change7("Hydrometer", 0, "Measuring Liquid Substance")
del7("Hydrometer", 1)
del dt7["FuelAtomizer"]
change7("Orchestra", 0, "agent of MakingInstrumentalMusic")
change7("VehicleDoor", 0, "Closing")
change7("VehicleDoor", 1, "Opening")
change7("MilitaryArtifact", 0, "MilitaryOrganization uses it")
change7("Organ", 0, "Purpose")
del7("CSGas", 2)
del7("CSGas", 0)
del dt7["Camshaft"]
change7("CriminalGang", 0, "agent of CriminalAction")
del dt7["TwoStrokeEngine"]
del dt7["AutomobileShock"]
del7("WaterHeater", 1)
del7("HighPrecisionWeapon", 2)
del7("HighPrecisionWeapon", 0)
del7("DryingDevice", 0)
change7("MilitaryVehicle", 0, "MilitaryOrganization uses it")
del7("Finger", 0)
del7("FanDevice", 0)
change7("Blueprint", 0, "represents Artifact")
change7("VideoDisplay", 0, "displays VideoRecording")
del7("VideoDisplay", 4)
del7("VideoDisplay", 3)
del7("VideoDisplay", 1)
change7("VocationalSchool", 0, "location of EducationalProcess Ending in OccupationalTrade")
add7("VocationalSchool", "teach students an &%OccupationalTrade")
change7("Marketplace", 0, "Measuring involving TactilePerception")
del7("Marketplace", 1)
del dt7["Carburetor"]
del7("Hammer", 1)
change7("AirIntake", 0, "origin of Transfer Air to Engine")
change7("AirIntake", 1, "contains Air")
change7("GunTrigger", 0, "Pulled causing Shooting AutomaticGun")
change7("MotorcycleGlove", 0, "agent of Driving Motorcycle wears it")

save_obj(dt7, "Telic_92")

dt7=load_obj("Telic_92")

change7("PerformanceStage", 0, "location of Demonstrating")
del7("BleederValve", 0)
change7("Washer", 2, "distribute the load of a threaded &%AttachingDevice")
del7("Washer", 1)
del7("Washer", 0)
change7("HandToolBox", 0, "contains HandTool")
change7("Buffet", 0, "contains nutrients for Human")
del7("SmokingDevice", 2)
del7("SmokingDevice", 1)
change7("SteamBath", 0, "location of Bathing")
del7("Supercharger", 0)
change7("WasherForBolt", 0, "contains Bolt")
del dt7["Cam"]
change7("Antibody", 0, "Destruction of Antigen")
change7("Prison", 0, "location of Confining Human by Government")
change7("Jallabiyyah", 0, "Man wears it")
del7("Armor", 4)
del7("Armor", 2)
del7("Armor", 1)
change7("Balloon", 0, "contains Gas")
del dt7["BrakeMasterCylinder"]
change7("Veneer", 0, "covers Entity")
change7("ArtStudio", 0, "Making ArtWork")
change7("Mailbox", 0, "destination of Mailing")
del dt7["Grease"]
dt7["GreaseGun"] = ["Putting Grease", "inject &%Grease"]
change7("MercantileOrganization", 0, "agent of Selling and CommercialService")
del dt7["ComputerTerminal"]
change7("Burrow", 0, "Animal inhabits it")
change7("ReferenceBook", 0, "consulted to answer specific factual questions")
change7("Khimar", 0, "Woman wears it")
change7("HotelFunctionRoom", 0, "Renting")
del7("HotelFunctionRoom", 1)
add7("HotelFunctionRoom", "is rented out and can be used for virtually any purpose")
change7("SafetyVest", 0, "increas the visibility of the wearer and so protect him from &%Injuring")
del7("SingleFamilyResidence", 0)
change7("HandTool", 0, "a particular purpose")
del7("SmokeDetector", 0)
change7("EducationalFacility", 0, "location of EducationalProcess")
del dt7["Mammal"]
change7("IceMachine", 0, "Process resulting in Ice")
del7("IceMachine", 1)
change7("PublicAddressSystem", 0, "RadiatingSound forall GroupOfPeople in a LandArea")
del7("PublicAddressSystem", 1)
change7("EmailMessage", 0, "be transmitted via electronic mail technology")
del dt7["ChemicalProduct"]
change7("DiningArea", 0, "location of Eating")
del dt7["EngineMAPSensor"]
change7("BathTub", 0, "contains Water")
change7("SeatBelt", 0, "prevents impact of the wearer into the interior surfaces of the &%Vehicle during rapid &%Decelerating")
change7("Wheelchair", 3, "Transportation by Human agent not capable of Walking")
del7("Wheelchair", 1)
del7("Wheelchair", 0)
# change7("InternalCombustionEngine", 2, "Combustion from Fuel")
# del7("InternalCombustionEngine", 3)
# del7("InternalCombustionEngine", 1)
# del7("InternalCombustionEngine", 0)
change7("RecordingStudio", 0, "location of Process resulting in Recording")
del dt7["BulletCartridge"]
del7("VendingMachine", 1)
change7("MultimediaProjector", 1, "Displaying Image on Flat Artifact ")
del7("MultimediaProjector", 0)
change7("Kitchen", 0, "location of Cooking")
change7("MotorcycleHelmet", 0, "Human Driving Motorcycle wears it")
del dt7["Gutrah"]
change7("Candle", 0, "resource of Fire")
change7("TireChanger", 0, "Putting Tire on WheelRim")
del7("TireChanger", 3)
del7("TireChanger", 2)
del7("TireChanger", 1)
del dt7["Crankshaft"]
change7("AbsoluteFilter", 0, "Removing from GasMixture")
del7("AbsoluteFilter", 3)
del7("AbsoluteFilter", 2)
del7("AbsoluteFilter", 1)
change7("Bomber", 0, "Transportation of ExplosiveDevice")
del7("Bomber", 2)
change7("Tire", 0, "covers WheelRim")
change7("FuelFilter", 0, "Removing NONFUEL from Solution")
del7("FuelFilter", 1)
del7("Respirator", 0)
change7("ParkingRegion", 0, "where &%TransportationDevice is kept temporarily")
del dt7["IgnitionControlModule"]
change7("Ambulance", 0, "Transportation of Human with DiseaseOrSyndrome and experiencer of Injuring")
del7("Ambulance", 0)
del7("AirConditioningCompressor", 1)
change7("CivilAffairs", 0, "agent of Guiding CivilMilitaryOperation or CivilAffairsActivity")
del dt7["ComputerLanguage"]
del7("Drum", 1)
change7("PoliticalPressureGroup", 0, "exert political pressure and have leaders who are involved in politics but not standing for election")
change7("RailVehicle", 0, "move on &%Railways")
change7("Abayah", 0, "Woman wears it")
change7("IgnitionCoil", 1, "ElectricTransmission causing Spark")
del7("IgnitionCoil", 0)
del dt7["CompoundSubstance"]
change7("Toilet", 0, "destination of Defecation or Urination")
del7("TemperatureControl", 0)
change7("Shimagh", 0, "Human wears it During coldSeasonInArea")
del7("EngineConnectingRod", 0)
change7("AllTerrainVehicle", 0, "Transportation On Roadway")
del7("AllTerrainVehicle", 1)
del7("Bolt", 2)
change7("RemoteControl", 0, "agent of ElectronicSignalling to Device")
del dt7["M60"]
change7("Kennel", 0, "location of Confining of DomesticAnimal")
del dt7["RockerArm"]

save_obj(dt7, "Telic_Final")




def change1(node, index, value):
    at[node][index] = value
    return
def del1(node, index):
    del at[node][index]
    return
def add1(node, value):
    at[node].append(value)
    return

del1("Steam", 1)
change1("Steam", 0, "Boiling Water")
del1("Sweat", 1)
del1("Text", 2)
del1("Text", 0)
change1("HormoneTSH", 0, "Process by ThyroidGland")
del1("HormoneTSH", 1)
change1("Vodka", 1, "Distilling CerealGrain")
del1("Vodka", 0)
del1("GeneticallyEngineeredOrganism", 1)
del1("Sketch", 0)
del1("PreparedFood", 1)
del1("Bone", 1)
del1("Brand", 1)
change1("Mycotoxin", 0, "BiologicalProcess by FungalAgent")
del1("Mycotoxin", 1)
del1("Organization", 0)
change1("Water", 1, "ChemicalSynthesis of Oxygen and Hydrogen")
del1("Water", 0)
del1("OrganismRemains", 1)
del1("Artifact", 2)
del1("Artifact", 1)
del1("MultipoleModel", 1)
del at["OrganicObject"]
change1("BirdEgg", 1, "SexualReproduction of Bird")
del1("BirdEgg", 0)
change1("WatercolorPicture", 1, "Painting by WatercolorPaint")
del1("WatercolorPicture", 0)
del1("Product", 1)
change1("Charcoal", 0, "Combustion of Wood")
del1("Charcoal", 1)
del1("Raisin", 0)
change1("Schnapps", 1, "Distilling Fruit")
del1("Schnapps", 0)
change1("Milk", 0, "Process by Female Mammal")
del1("Milk", 1)
del1("ReproductiveBody", 1)
del1("ReadOnlyMemoryDataStorage", 1)
change1("SodiumChloride", 1, "ChemicalSynthesis of Sodium and Chlorine")
del1("SodiumChloride", 0)
del1("Canyon", 1)
change1("CottonFabric", 0, "Making from Cotton")
del1("CottonFabric", 1)
change1("Wool", 0, "Making from Hair of Sheep")
del1("Wool", 1)
del1("Pancake", 1)
del1("Lesion", 1)
change1("Urine", 0, "PhysiologicProcess by Kidney")
del1("Urine", 1)
change1("Paper", 0, "Making from Cellulose")
del1("Paper", 1)
del1("Announcement", 0)
del at["ContentBearingObject"]
del at["VisualContentBearingObject"]
change1("Butter", 0, "Cooking Milk")
del1("Butter", 1)
del1("Omelette", 1)
change1("Toxin", 1, "BiologicalProcess by ToxicOrganism")
del1("Toxin", 0)
del1("Vinegar", 0)
del at["TwoDimensionalObject"]
change1("Hay", 0, "Making from Grass")
del1("Hay", 1)
del1("SyntheticSubstance", 0)
change1("Feces", 1, "PhysiologicProcess by Intestine")
del1("Feces", 0)
del1("ArtWork", 0)
change1("Hormone", 0, "Process by Gland")
del1("Hormone", 1)
del1("AbnormalAnatomicalStructure", 1)
change1("Silk", 0, "Making from part of Larval Insect")
del1("Silk", 1)
change1("Flour", 1, "IntentionalProcess from CerealGrain")
del1("Flour", 0)
change1("Brandy", 1, "Distilling Wine")
del1("Brandy", 0)
del at["Substance"]
del1("BodyPart", 0)
change1("Scar", 0, "OrganOrTissueProcess on Lesion")
del1("Scar", 1)
change1("SearchQuery", 1, "Questioning from SearchEngine")
del1("SearchQuery", 0)
change1("Leather", 1, 'Making from Skin')
del1("Leather", 0)
change1("Excrement", 1, "PhysiologicProcess by Organism")
del1("Excrement", 0)
del1("Organ", 1)
change1("Tequila", 1, "Distilling BlueAgave")
del1("Tequila", 0)
del1("Blueprint", 2)
change1("TearSubstance", 0, "Process by Eye")
del1("TearSubstance", 1)
change1("OilPicture", 0, "Painting by OilPaint")
del1("OilPicture", 1)
change1("Cholesterol", 0, "BiologicalProcess in Liver")
del1("Cholesterol", 1)
del1("Exhaust", 1)
change1("Burrow", 0, "Process by Animal and not Human")
del1("Burrow", 1)
del1("FaxMessage", 0)
change1("Rum", 0, "Distilling SugarCane")
del1("Rum", 1)
change1("Whiskey", 1, "Distilling CerealGrain")
del1("Whiskey", 2)
del1("Whiskey", 0)
del1("PureSubstance", 1)
change1("BreadOrBiscuit", 1, "Baking Dough")
del1("BreadOrBiscuit", 0)
del1("Smoke", 0)
del1("Cave", 0)
change1("Honey", 1, "PhysiologicProcess by Bee")
del1("Honey", 1)
change1("CompoundSubstance", 1, "ChemicalSynthesis of two ElementalSubstance")
del1("CompoundSubstance", 1)

save_obj(at, "Agentive_Final")





findDocumentation("RockerArm")








telicList = []


for i in dt7.items():
    if i[1] and type(i[1]) == list:
        for j in i[1]:
            telicList.append((i[0], j))
    elif i[1] and type(i[1]) == str:
        telicList.append((i[0], i[1]))

save_obj(telicList, "telicFinal")

load_obj("telicTest1")


agentiveList = []
for i in at.items():
    if i[1] and type(i[1]) == list:
        for j in i[1]:
            agentiveList.append((i[0], j))
    elif i[1] and type(i[1]) == str:
        agentiveList.append((i[0], i[1]))

save_obj(agentiveList, "agentiveFinal")


constitutiveList = []
for i in ct.items():
    if i[1] and type(i[1]) == list:
        for j in i[1]:
            constitutiveList.append((i[0], j))
    elif i[1] and type(i[1]) == str:
        constitutiveList.append((i[0], i[1]))

save_obj(constitutiveList, "constitutiveTest")


first_25 = telicList[:25]
second_25 = telicList[26:50]
# writeFile("telic25.txt", first_25)

save_obj(first_25, "telic_25")
save_obj(second_25, "telic_50")
save_obj(telicList, "telicset1")

# abc = load_obj("telic_25")



findDocumentation("PictureFrame")



teldoc = {}
for i in telicList:
    teldoc[i[0]] = findDocumentation(i[0])
save_obj(teldoc, "teldoc")

agf = load_obj("agentiveFinal")
agedoc = {}
for i in agf:
    agedoc[i[0]] = findDocumentation(i[0])
save_obj(agedoc, "agedoc")

conf = load_obj("constitutiveTest")
condoc = {}
for i in conf:
    condoc[i[0]] = findDocumentation(i[0])
save_obj(condoc, "condoc")

"""



