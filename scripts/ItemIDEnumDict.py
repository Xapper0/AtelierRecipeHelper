import csv

class ItemIDEnumDict:
    def __init__(self):
        self.enumToID = {}
        self.englishToID = {}

def createItemIDEnumDict(dictPath):
    itemIDEnumDict = ItemIDEnumDict()
    with open(dictPath) as dictFile:
        dictCSV = csv.reader(dictFile)
        for row in dictCSV:
            if row[1] != "":
                itemIDEnumDict.englishToID[row[1].encode("ascii", errors="ignore").decode()] = row[2]
                itemIDEnumDict.enumToID[row[0]] = row[2]
    return itemIDEnumDict
