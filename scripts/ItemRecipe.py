import xml.etree.ElementTree as ET
import ItemIDEnumDict
import csv
from pprint import pprint

itemIDEnumDict = ItemIDEnumDict.createItemIDEnumDict("data/ryza_enums_id.csv")

MAX_EFFECT_COUNT = 4
MAX_CAT_COUNT = 4

#Attribute names for the item data
NAME_ID = "nameID"
CATEGORY = "cat_"
ITEM_TYPE = "kindTag"

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
DLC = "ITEM_DLC"

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
class RecipeNode:
    def __init__(self):
        self.itemUsed = None #The item used in the synthesis
        self.children = []
        self.unlock = None #The unlock requirements of the node (if any)
        self.synthBoosts = []

#Data involved in unlocking the node
class SynthUnlock:
    def __init__(self, cost, element):
        self.cost = cost
        self.element = element

#What boost the node gives to the item
class SynthBoost:
    def __init__(self, cost, element, name):
        self.cost = cost
        self.element = element
        self.name = name

#The recipe itself
class Recipe:
    def __init__(self, recipeMeta):
        self.meta = recipeMeta
        self.nodes = {}

#What the item involves
class Item:
    def __init__(self, stringID, categories, itemType, recipe):
        self.stringID = stringID
        self.categories = categories
        self.itemType = itemType
        self.recipe = recipe

def createRMetaDict(metaPath):
    """Creates a dictionary of Recipe Meta from enum to the RecipeMeta

    Args:
        metaPath (str): Path to the recipe meta data

    Returns:
        dict of str : RecipeMeta: dictionary from enum to RecipeMeta
    """
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

def getEffects(itemAttrib):
    """Gets the effects and appends them into an list

    Args:
        itemAttrib (dict of str:str): the effects of the item

    Returns:
        list of str: the effects of the item
    """
    effectList = []
    for effectNo in range(MAX_EFFECT_COUNT):
        addEff = EFFECT + str(effectNo)
        if addEff in itemAttrib:
            effectList.append(itemAttrib.get(addEff))
        else:
            effectList.append(None)
    return effectList

def createRecipes(recipeMetaDict, recipePath, allowDLC = False):
    """Creates the recipes of an item

    Args:
        recipeMetaDict (dict of str : RecipeMeta): A recipe meta dictionary
        recipePath (str): The path to where the recipes are stored
        allowDLC (bool, optional): Whether or not to allow DLCs. Defaults to False.

    Returns:
        dict of str to Recipe: A dictionary of enums to the recipe
    """
    xmlp = ET.XMLParser(encoding='utf-8')
    tree = ET.parse(recipePath, parser=xmlp)
    root = tree.getroot()

    recipes = {}

    #Should be refactored
    for recipeData in root:
        recipeName = recipeData.attrib[RECIPE_NAME]

        if recipeName not in itemIDEnumDict.enumToID: #Some items aren't in the enums file
            print(recipeName, "not found in enums")
            continue

        recipe = Recipe(recipeMetaDict[recipeName])
        recipes[itemIDEnumDict.enumToID[recipeName]] = recipe
        
        if recipeData.tag != RECIPE_TAG: #Used to check that the right recipe was gotten
            print("Expected:", RECIPE_TAG, "got:", recipeData)
            continue
        
        nodeNo = -1
        for node in recipeData:
            nodeNo += 1
            recipeNode = RecipeNode()

            #Getting the unlock conditions and what connects to the node
            if nodeNo != 0: 
                unlockInfo = node.find(UNLOCK)
                if unlockInfo == None or unlockInfo.get(UNLOCK_CONNECT) == None: 
                    #Nothing connects to the node so is invalid
                    continue
                elif unlockInfo.attrib.get(UNLOCK_COST) != None:
                    recipeNode.unlock = SynthUnlock(unlockInfo.attrib[UNLOCK_COST], unlockInfo.attrib[ELEMENT])

            #Getting the item or category used in the node
            if ITEM_USED in node.attrib:
                recipeNode.itemUsed = recipe.meta.matsUsed[int(node.attrib[ITEM_USED])]
            else:
                recipeNode.itemUsed = node.attrib[EXTRA_ITEM_USED]
                if not allowDLC and recipeNode.itemUsed.startswith(DLC):
                    #The node requires a DLC only item, so is skipped
                    continue

            for element in node:
                #Gets the children of the node
                if element.tag == CHILDREN:
                    childrenString = element.attrib[CHILDREN_STRING][:-1] #There is an extra comma at the end so it is removed
                    children = childrenString.split(",")
                    recipeNode.children = list(filter(("-1").__ne__, children))
                #Getting the effects and other boosts from the node
                elif element.tag == BOOST:    
                    boostType = int(node.attrib[BOOST_TYPE])
                    i = 0
                    while (BOOST_COST + str(i)) in element.attrib:
                        boostCost = element.attrib[BOOST_COST + str(i)]
                        boostElem = node.attrib[ELEMENT]
                        boostEffectTag = BOOST_EFFECT + str(i)
                        boostName = getBoostName(boostType, element.attrib[boostEffectTag], recipe)

                        recipeNode.synthBoosts.append(SynthBoost(boostCost, boostElem, boostName))
                        i += 1
            recipe.nodes[nodeNo] = recipeNode
    return recipes

def createItems(itemPath, recipes):
    """Creates the items and applies the recipes to them (if applicable)

    Args:
        itemPath (str): the path to where the items are stored
        recipes (dict of str : Recipe): the recipes to attach to the items

    Returns:
        [list of Item]: The items in the file
    """
    xmlp = ET.XMLParser(encoding='utf-8')
    tree = ET.parse(itemPath, parser=xmlp)
    root = tree.getroot()
    items = []
    for item in root:
        if NAME_ID in item.attrib:
            nameID = item.attrib[NAME_ID]

            #Getting the categories
            categories = []
            for i in range(MAX_CAT_COUNT):
                categoryID = CATEGORY + str(i)
                if categoryID in item.attrib:
                    categoryEnum = item.attrib.get(categoryID)
                    categories.append(itemIDEnumDict.enumToID[categoryEnum])
                else:
                    break
            items.append(Item(nameID, categories, item.attrib[ITEM_TYPE], recipes.get(nameID)))
    return items

def getBoostName(boostType, boostEffect, recipe):
    """Gets the name of the boost

    Args:
        boostType (int): The type of the boost as a number
        boostEffect (str): The effect of the boost
        recipe (Recipe): The recipe of the item of the boost

    Returns:
        str: The name of the boost
    """
    if boostType >= 0 and boostType <= 3: #adds effect
        return recipe.meta.effects[boostType][int(boostEffect)]
    elif boostType == 4: #adds quality
        return "Quality +" +  boostEffect
    elif boostType == 5: #adds trait
        return "Trait Up"
    elif boostType == 6: #adds recipe
        return boostEffect[len("ITEM_RECIPE_"):]
    elif boostType == 7: #lowers level
        return "Level -" + boostEffect
    elif boostType == 8: #lowers CC cost
        return "CC -" + boostEffect
    elif boostType == 9: #Increases HP
        return "HP + " + boostEffect
    elif boostType == 11: #Increases attack
        return "ATK + " + boostEffect
    elif boostType == 12: #Increases defense
        return "DEF + " + boostEffect
    elif boostType == 13: #Increases speed
        return "SPD + " + boostEffect
    elif boostType == 14: #Increase role Offense level
        return "Offense LV. + " + boostEffect
    elif boostType == 15: #Increase role Defense level
        return "Defense LV. + " + boostEffect
    elif boostType == 16: #Increase role Support level
        return "Support LV. + " + boostEffect
    else:
        print("Unexpected boostType:",boostType)
        return ""

def createItemRecipe(recipeMetaPath, recipePath, itemCatPath):
    """Creates Items with their recipes

    Args:
        recipeMetaPath (str): Path to the recipe meta data
        recipePath (str): Path to the recipe data
        itemCatPath (str): Path to the item category data

    Returns:
        [list of Item]: The items in the file
    """
    recipeMetaDict = createRMetaDict(recipeMetaPath)
    recipes = createRecipes(recipeMetaDict, recipePath)
    return createItems(itemCatPath, recipes)