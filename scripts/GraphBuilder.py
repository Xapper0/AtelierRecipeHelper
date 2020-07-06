import xml.etree.ElementTree as ET
from pprint import pprint

MAX_EFFECT_COUNT = 4

#Attribute names for the meta data
NEW_ITEM = "ItemTag"
MAKE_NUM = "MakeNum"
HOURS_NEEDED = "Hour"
MIN_MATS = "NeedNum"
SYN_CAT = "RecipeCategory"
MAT = "MatTag"
EFFECT = "AddEff"
START_EFFECT = "MassEffect"
HAS_DATA = "HasData"

#Attribute and tag names for recipe data
RECIPE_TAG = "FieldData"
RECIPE_NAME = "tag"
ELEMENT = "elem"
NODE = "Ring"
BOOST_TYPE = "type"
ITEM_USED = "restrict"
EXTRA_ITEM_USED = "ex_material"
CHILDREN = "Child"
CHILDREN_STRING = "indexes"
UNLOCK = "Connect"
UNLOCK_COST = "val"
UNLOCK_CONNECT = "idx"
BOOST = "Param"
BOOST_COST = "e"
BOOST_EFFECT = "v"

#The information about the recipe
class RecipeMeta:
    def __init__(self):
        self.recipeName = None
        self.makeNum = None
        self.hoursNeeded = None
        self.minMats = None
        self.synCategory = None
        self.matsUsed = []
        self.effects = []
        self.startEffects = []

#The synthesis node
class SynthNode:
    def __init__(self):
        self.itemUsed = None #The item used in the synthesis
        self.children = []
        self.unlock = None #The unlock requirements of the node (if any)
        self.synthBoosts = []

#
class SynthUnlock:
    def __init__(self, cost, element):
        self.cost = cost
        self.element = element

class SynthBoost:
    def __init__(self, cost, element, name):
        self.cost = cost
        self.element = element
        self.name = name

class Recipe:
    def __init__(self, recipeMeta):
        self.meta = recipeMeta
        self.nodes = []

#Creates a dictionary of Recipe Meta
def createRMetaDict(metaPath):
    xmlp = ET.XMLParser(encoding='utf-8')
    tree = ET.parse(metaPath, parser=xmlp)
    root = tree.getroot()

    recipeMetaDict = {}
    currentRecipe = None

    for item in root:
        if NEW_ITEM in item.attrib: #new recipe meta
            if HAS_DATA not in item.attrib: #ignoring placeholders
                continue

            currentRecipe = RecipeMeta()
            recipeMetaDict[item.attrib.get(NEW_ITEM)] = currentRecipe
            
            currentRecipe.recipeName = item.attrib.get(NEW_ITEM)
            currentRecipe.makeNum = item.attrib.get(MAKE_NUM)
            currentRecipe.hoursNeeded = item.attrib.get(HOURS_NEEDED)
            currentRecipe.minMats = item.attrib.get(MIN_MATS)
            currentRecipe.synCategory = item.attrib.get(SYN_CAT)

            currentRecipe.matsUsed.append(item.attrib.get(MAT))
            currentRecipe.effects.append(getEffects(item.attrib))
            currentRecipe.startEffects.append(item.attrib.get(START_EFFECT))

        else: #addition to the recipe meta
            if MAT in item.attrib:
                currentRecipe.matsUsed.append(item.attrib.get(MAT))

            effects = getEffects(item.attrib)
            if effects:
                currentRecipe.effects.append(effects)
            
            if START_EFFECT in item.attrib:
                currentRecipe.startEffects.append(item.attrib.get(START_EFFECT))

    return recipeMetaDict

#Gets the effects and appends them into an array
def getEffects(itemAttrib):
    effectList = []
    for effectNo in range(MAX_EFFECT_COUNT):
        addEff = EFFECT + str(effectNo)
        if addEff in itemAttrib:
            effectList.append(itemAttrib.get(addEff))
        else:
            effectList.append(None)
    return effectList

def createRecipes(recipeMetaDict, recipePath):
    xmlp = ET.XMLParser(encoding='utf-8')
    tree = ET.parse(recipePath, parser=xmlp)
    root = tree.getroot()

    recipes = []

    for recipeData in root:
        recipe = Recipe(recipeMetaDict[recipeData.attrib[RECIPE_NAME]])
        recipes.append(recipe)

        if recipeData.tag != RECIPE_TAG:
            print("Expected:", RECIPE_TAG, "got:", recipeData)
            continue
        
        firstNode = True

        for node in recipeData:
            synthNode = SynthNode()
            recipe.nodes.append(synthNode)
            
            if len(node.attrib) < 3:
                continue

            if not firstNode: #Getting the unlock conditions
                unlockInfo = node.find(UNLOCK)
                if unlockInfo == None or unlockInfo.get(UNLOCK_CONNECT) == None:
                    continue
                elif recipeData.attrib.get(UNLOCK_COST) != None:
                    synthNode.unlock = SynthUnlock(tag.attrib[UNLOCK_COST], tag.attrib[ELEMENT])
            else:
                firstNode = False

            if ITEM_USED in node.attrib:
                synthNode.itemUsed = recipe.meta.matsUsed[int(node.attrib[ITEM_USED])]
            else:
                synthNode.itemUsed = node.attrib[EXTRA_ITEM_USED]

            for tag in node:
                if tag.tag == CHILDREN:
                    childrenString = tag.attrib[CHILDREN_STRING][:-1] #There is an extra comma at the end so it is removed
                    children = childrenString.split(",")
                    synthNode.children = list(filter(("-1").__ne__, children))

                elif tag.tag == BOOST:    
                    boostType = int(node.attrib[BOOST_TYPE])
                    if boostType >= 0 and boostType <= 3:
                        i = 0
                        while (BOOST_COST + str(i)) in tag.attrib:
                            boostCost = tag.attrib[BOOST_COST + str(i)]
                            boostElem = node.attrib[ELEMENT]
                            boostName = recipe.meta.effects[boostType][int(tag.attrib[BOOST_EFFECT + str(i)])]
                            if boostName == None:
                                print(recipeData.attrib, tag.attrib, recipe.meta.effects, boostType,"\n")
                            synthNode.synthBoosts.append(SynthBoost(boostCost, boostElem, boostName))
                            i += 1

    return recipes
    

if __name__ == "__main__":
    recipeMetaDict = createRMetaDict("data/itemrecipedata.xml")
    recipes = createRecipes(recipeMetaDict, "data/mixfielddata.xml")
