import csv

class ItemIDEnumDict:
    def __init__(self):
        self.enumToID = {}
        self.englishToID = {}
        self.addCat = {}

def createItemIDEnumDict(dictPath):
    itemIDEnumDict = ItemIDEnumDict()
    with open(dictPath) as dictFile:
        dictCSV = csv.reader(dictFile)
        for row in dictCSV:
            itemIDEnumDict.englishToID[row[1].encode("ascii", errors="ignore").decode()] = row[2]
            itemIDEnumDict.enumToID[row[0]] = row[2]
            if row[0].startswith("ITEM_EFF_ADD_CATEGORY"):
                #easiest way for me to connect the add categories to the string id of what they add
                itemIDEnumDict.addCat[row[0]] = itemIDEnumDict.englishToID[row[1][len("Add "):]] 
    return itemIDEnumDict
