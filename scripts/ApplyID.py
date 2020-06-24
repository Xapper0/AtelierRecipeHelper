import csv
import sys
import xml.etree.ElementTree as ET
import glob
from enum import Enum

STRING_ID = "String_No"
TRANSLATION = "Text"

class ryzaEnumStarters(Enum):
    MATERIAL = "ITEM_MAT"
    MIX = "ITEM_MIX"
    WEAPON = "ITEM_WEAPON"
    ARMOUR = "ITEM_ARMOR"
    ACCESSORY = "ITEM_ACCESSORY"
    KEY = "ITEM_KEY"
    CATEGORY = "ITEM_CATEGORY"
    EFFECT = "ITEM_EFF"
    TRAIT = "ITEM_POTENTIAL"

def joinXMLToCSV(pathPattern, writePath):
    with open(writePath, mode="w") as writeFile:
        writer = csv.writer(writeFile, lineterminator="\n")
        for path in glob.glob(pathPattern):
            tree = ET.parse(path)
            root = tree.getroot()
            for item in root:
                row = []
                row.append((item.find(".").attrib[STRING_ID]).encode("ascii", errors="ignore").decode())
                row.append((item.find(".").attrib[TRANSLATION]).encode("ascii", errors="ignore").decode())
                writer.writerow(row)

def applyID(startNumber, enumsPath):
    with open(enumsPath) as enumsFile, open(enumsPath[:-4] + "_id.csv", mode="w") as writeFile:
        reader = csv.reader(enumsFile)
        writer = csv.writer(writeFile, lineterminator="\n")
        for row in reader:
            row.append(startNumber)
            writer.writerow(row)
            startNumber = startNumber + 1

def testIDs(enumsPath, translatedPath):
    # Creating dictionary
    translationDictionary = {}

    with open(translatedPath) as translatedFile:
        translated = csv.reader(translatedFile)
        for row in translated:
            translationDictionary[row[0].encode("ascii", errors="ignore").decode()] = row[1]

    with open(enumsPath) as enumsFile:
        reader = csv.reader(enumsFile)
        for row in reader:
            if row[1] == "":
                continue
            
            # row[1] = row[1].encode("ascii", errors="ignore").decode()
            if row[2] in translationDictionary and row[1] != translationDictionary.get(row[2]):
                print(row, "Does not have the right id", translationDictionary.get(row[0]))

            # if row[1] in translationDictionary:
            #     row[1] = translationDictionary.get(row[1])
            #     usedDictionary[row[1]] = row[0]
            #     writer.writerow(row)
            # else:
            #     print(row, "not found")

if __name__ == "__main__":
    applyID(6750209, "data/ryza_enums.csv")
    testIDs("data/ryza_enums_id.csv", "data/str_item.csv")