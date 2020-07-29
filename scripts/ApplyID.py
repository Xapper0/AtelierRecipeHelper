import csv
import xml.etree.ElementTree as ET
import StringIDToLang

def applyID(startNo, idJumps, enumsPath):
    """Adds the string ids to the enums file 

    Args:
        startNo (int): The id to start with
        idJumps (dict of str : int): When the id should change for a given enum
        enumsPath (str): The path to the enums file
    """
    with open(enumsPath) as enumsFile, open(enumsPath[:-4] + "_id.csv", mode="w") as writeFile:
        reader = csv.reader(enumsFile)
        writer = csv.writer(writeFile, lineterminator="\n")

        stringID = startNo
        for row in reader:
            if row[0] in idJumps:
                stringID = idJumps[row[0]]
            row.append(stringID)
            writer.writerow(row)
            stringID = stringID + 1

def testIDs(enumsPath, translationDictionary):
    """Used to test that the ID is correctly applied by comparing English names

    Args:
        enumsPath (str): The path to the enums file where the id is also stored
        translationDictionary (dict of int : str): The dictionary the compare the English name with
    """
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

    stringIDToLang = StringIDToLang.createStringIDToLang("data/strcombineall.xml")
    testIDs("data/ryza_enums_id.csv", stringIDToLang)