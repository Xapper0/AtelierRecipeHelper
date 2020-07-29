import csv
import sys
import xml.etree.ElementTree as ET
import glob
import StringIDToLang
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

def applyID(startNo, idJumps, enumsPath):
    with open(enumsPath) as enumsFile, open(enumsPath[:-4] + "_id.csv", mode="w") as writeFile:
        reader = csv.reader(enumsFile)
        writer = csv.writer(writeFile, lineterminator="\n")

        for row in reader:
            if row[0] in idJumps:
                startNo = idJumps[row[0]]
            row.append(startNo)
            writer.writerow(row)
            startNo = startNo + 1

def testIDs(enumsPath, translationDictionary):
    with open(enumsPath) as enumsFile:
        reader = csv.reader(enumsFile)
        for row in reader:
            if row[1] == "":
                continue
            if row[2] not in translationDictionary:
                print(row, "Does not exist in the dictionary")
                break
            elif row[1] != translationDictionary.get(row[2]):
                print(row, "Does not have the right id", translationDictionary.get(row[0]))              

if __name__ == "__main__":
    idJumps = {
        "ITEM_CATEGORY_LIQUID":6815745,
        "ITEM_EFF_DAMAGE_UNI_1":6881281,
        "ITEM_POTENTIAL_QUALITY_UP_01":6946817,
        "MONSTER_PUNI_00":19791873,
        "ITEM_KIND_MATERIAL":7012353
    }
    applyID(6750209, idJumps, "data/ryza_enums.csv")
    # applyID(6750209, "data/itemcat.csv")
    stringIDToLang = StringIDToLang.createStringIDToLang("data/strcombineall.xml")
    testIDs("data/ryza_enums_id.csv", stringIDToLang)