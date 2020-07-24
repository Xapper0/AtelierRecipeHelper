import xml.etree.ElementTree as ET

STRING_ID = "String_No"
TEXT = "Text"

def createStringIDToLang(allStringPath):
    xmlp = ET.XMLParser(encoding='utf-8')
    tree = ET.parse(allStringPath, parser=xmlp)
    root = tree.getroot()
    stringIDToLang = {}
    
    for string in root:
        stringIDToLang[string.attrib.get(STRING_ID)] = string.attrib.get(TEXT)

    return stringIDToLang