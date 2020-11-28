import praw, re, string, requests, numpy
from collections import Counter
from strsimpy.jaro_winkler import JaroWinkler


def getHeroNameList():
    r = requests.get('https://www.ffrktoolkit.com/ffrk-api/api/v1.0/IdLists/Character')
    heroNameList = [entry['Value'] for entry in r.json()]
    removeNames = ['Red Mage', 'Thief (Core)', 'Thief (I)', 'Cloud of Darkness', 'Cecil (Dark Knight)', 'Cecil (Paladin)',
                   'Cid (IV)', 'Gogo (V)', 'Gogo (VI)', 'Cid (VII)', 'Cid Raines', 'Cid (XIV)', 'Shadowsmith', 'Shared']
    addNames = ['Thief', 'CoD', 'Decil', 'Pecil', 'Cid', 'Gogo']
    addNicknames = ['OK', 'Greg', 'Nanaki', 'Laugh', 'Kitty', 'Raines', 'TGC']
    for name in removeNames:
        heroNameList.remove(name)
    heroNameList.extend(addNames)
    heroNameList.extend(addNicknames)
    return heroNameList

def cleanHeroName(heroName, heroNameList, strsim):
    slangDict = {'OK':'Onion Knight', 'Greg':'Gilgamesh', 'Nanaki':'Red XIII', 'Laugh':'Tidus', 'Raines':'Cid', 'TGC':'Orlandeau'}
    matchTuples = sorted([(name, strsim.similarity(name, heroName)) for name in heroNameList], key=lambda tup: tup[1], reverse=True)
    matchScores = numpy.array([tuple[1] for tuple in matchTuples])
    matchCandidate = matchTuples[0]
    if ((matchCandidate[1] >= 0.85) or (matchCandidate[1] >= (numpy.mean(matchScores) + 2*numpy.mean(matchScores)))):
        if matchCandidate[0] in slangDict.keys():
            cleanedHeroName = slangDict[matchCandidate[0]]
        else:
            cleanedHeroName = matchCandidate[0]
    else:
        cleanedHeroName = 'ParseFail'
    # print(matchTuples) # debug
    # print('Match score mean: {}'.format(numpy.mean(matchScores)))
    # print('Match score median: {}'.format(numpy.median(matchScores)))
    # print('Match score std dev: {}'.format(numpy.std(matchScores)))
    return cleanedHeroName

def cleanSbNames(sbNameList):
    cleanList = []
    for sbName in sbNameList:
        sbNameCheck = sbName.lower()
        if 'lbo' in sbNameCheck:
            cleanList.append('LBO')
        elif 'limit' in sbNameCheck:
            cleanList.append('LBO')
        elif 'sync' in sbNameCheck:
            cleanList.append('SASB')
        elif 'sasb' in sbNameCheck:
            cleanList.append('SASB')
        elif 'aasb' in sbNameCheck:
            cleanList.append('AASB')
        elif 'awake' in sbNameCheck:
            cleanList.append('AASB')
        elif 'woke' in sbNameCheck:
            cleanList.append('AASB')
        elif 'glint+' in sbNameCheck:
            cleanList.append('GSB+')
        elif 'g+' in sbNameCheck:
            cleanList.append('GSB+')
        elif 'csb' in sbNameCheck:
            cleanList.append('CSB')
        elif 'chain' in sbNameCheck:
            cleanList.append('CSB')
        elif 'aosb' in sbNameCheck:
            cleanList.append('AOSB')
        elif 'usb' in sbNameCheck:
            cleanList.append('USB')
        elif 'osb' in sbNameCheck:
            cleanList.append('OSB')
        elif 'glint' in sbNameCheck:
            cleanList.append('GSB')
        elif 'bsb' in sbNameCheck:
            cleanList.append('BSB')
        elif 'burst' in sbNameCheck:
            cleanList.append('BSB')
        elif 'ssb' in sbNameCheck:
            cleanList.append('SSB')
        elif 'unique' in sbNameCheck:
            cleanList.append('Unique')
    return cleanList


def parseTeamTable(commentBody, heroNameList, strsim):
    heroRowOffset = 2
    numHeroRows = 5
    heroIdx = 1
    lmIdx = 4
    sbIdx = -2

    bodyLines = commentBody.split('\n')
    tableStartIdx = [idx for idx, text in enumerate(bodyLines) if text[0:5].lower() == '|hero']
    if tableStartIdx == []:
        return {}  # return empty sb dict if this comment has no mastery team table we can detect
    else:
        try:
            # print(bodyLines)
            tableStartIdx = tableStartIdx[0]
            tableLines = bodyLines[tableStartIdx+heroRowOffset:tableStartIdx+heroRowOffset+numHeroRows]
            splitTable = [line.split('|') for line in tableLines]
            heroNames = [re.split('[, ]', line[heroIdx])[0] for line in splitTable]
            heroNames = [cleanHeroName(name, heroNameList, strsim) for name in heroNames]
            sbNamesRaw = [re.sub(r'\([^)]*\)', '', line[sbIdx]).replace(',', ' ').replace('/', ' ').split() for line in splitTable]  # remove stuff inside parens
            sbNamesClean = [cleanSbNames(sbNamesList) for sbNamesList in sbNamesRaw]
            sbDict = {re.sub('[^A-Za-z0-9]+', '', k).lower().capitalize():v for (k, v) in zip(heroNames, sbNamesClean)}  # standardize hero name formatting some
            return sbDict
        except:
            return {}


def appendTableHeader(outputLines, sbTypes):
    titleString = ''.join(['|Hero|Used|', '|'.join(sbTypes), '|\n'])
    outputLines.append(titleString)
    alignmentStringList = [':-:' for item in titleString.split('|')]
    alignmentString = '|'.join(alignmentStringList)
    outputLines.append(''.join([alignmentString[3:-3], '\n']))  # trim off ends
    return


def appendHeroRow(outputLines, heroName, sbTypes, nameCounts, sbCountDict):
    heroCount = str(nameCounts[heroName])
    heroSbCountDict = sbCountDict[heroName]
    sbCounts = [str(heroSbCountDict[sbType]) if sbType in heroSbCountDict.keys() else '0' for sbType in sbTypes]
    outputLines.append(''.join(['|{}|{}|'.format(heroName, heroCount), '|'.join(sbCounts), '|\n']))
    return


def appendAveragesRow(outputLines, sbTypes, sbCounts, totalTeams):
    sbAverages = ['**{:.2f}**'.format(sbCounts[sbType]/totalTeams) if sbType in sbCounts.keys() else '**0**' for sbType in sbTypes]
    outputLines.append(''.join(['|{}|{}|'.format('**Average**', '**n/a**'), '|'.join(sbAverages), '|\n']))
    return


def snipRealm(threadTitle):

    return realm

# You'll need to get your own client id and secret from Reddit - it's quick:
# https://www.geeksforgeeks.org/how-to-get-client_id-and-client_secret-for-python-reddit-api-registration/
reddit = praw.Reddit(
     client_id="<Put client ID here>",
     client_secret="<Put client secret here>",
     user_agent="FFRK mastery scraper by /u/mutlibottlerocket"
)

threadIds = ['jkj12l', 'idrf6n', 'jxb735', 'i12tyd', 'iqk212', 'jc5k7a', 'h7ybrg', 'i97f4x', 'j7kwp4', 'hshnwo']  # this has to be updated as new Dreambreakers release
sbTypes = ['LBO', 'SASB', 'AASB', 'GSB+', 'CSB', 'AOSB', 'USB', 'OSB', 'GSB', 'BSB', 'SSB', 'Unique']  # cleanSbNames() maps to these
heroNameList = getHeroNameList()
strsim = JaroWinkler()  # string similarity module for catching typos/abbreviations

outputLines = []  # buffer to put output strings into
summaryLines = ['#Summary table\n\n\n']
appendTableHeader(summaryLines, sbTypes)
summaryLines[-2] = summaryLines[-2].replace('|Hero|Used', '|Realm')
summaryLines[-1] = summaryLines[-1][4:]
for threadId in threadIds:
    submission = reddit.submission(id=threadId)
    threadTitle = submission.title
    print(threadTitle)
    realm = threadTitle[threadTitle.find("(")+1:threadTitle.find(")")]  # brittle way of snipping out realm from DB thread titles
    topLevelComments = list(submission.comments)
    sbDicts = [parseTeamTable(comment.body, heroNameList, strsim) for comment in topLevelComments]
    flatNames = [item for dict in sbDicts for item in dict.keys()]
    nameCounts = Counter(flatNames)

    sbCountDict = {}
    for name in nameCounts.keys():
        flatSbs = [item for dict in sbDicts if name in dict.keys() for item in dict[name]]
        sbCountDict[name] = Counter(flatSbs)

    globalFlatSbs = [item for dict in sbDicts for key in dict.keys() for item in dict[key]]  # for averages
    sbCounts = Counter(globalFlatSbs)
    totalTeams = len(['' for dict in sbDicts if dict != {} ])

    # write output to buffer list
    outputLines.append('#[{}](https://redd.it/{})\n\n'.format(''.join(filter(lambda x: x in string.printable, submission.title)), threadId))
    outputLines.append('Number of clears parsed: {}\n\n\n'.format(totalTeams))
    appendTableHeader(outputLines, sbTypes)
    namesByFreq = [pair[0] for pair in nameCounts.most_common()]
    for heroName in namesByFreq:
        appendHeroRow(outputLines, heroName, sbTypes, nameCounts, sbCountDict)
    appendAveragesRow(outputLines, sbTypes, sbCounts, totalTeams)
    appendAveragesRow(summaryLines, sbTypes, sbCounts, totalTeams)
    summaryLines[-1] = summaryLines[-1].replace('Average', realm).replace('|**n/a**', '').replace('**','')
    outputLines.append('\n\n\n')

# prepend SB averages summary table
summaryLines.append('\n\n\n')
outputLines[:0] = summaryLines

# write output to text file
with open('output.txt', 'w') as f:
    f.writelines(outputLines)
print('Script finished!')