from neo4j import GraphDatabase
import ItemRecipe
import ItemIDEnumDict
import StringIDToLang
import csv

class RyzaDB:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)

    def close(self):
        self.driver.close()
    
    def writeElements(self):
        """Writes the elements to the database
        """
        with self.driver.session() as session:
            session.run("CREATE (:Element {string_id:'4063340', element_id:0}) " #fire
                        "CREATE (:Element {string_id:'4063341', element_id:1}) " #ice
                        "CREATE (:Element {string_id:'4063342', element_id:2}) " #lightning
                        "CREATE (:Element {string_id:'4063343', element_id:3}) ")#wind
    
    def writeCats(self, categoryIDs):
        """Writes the categories to the database

        Args:
            categoryIDs (list of str): list of category ids
        """
        with self.driver.session() as session:
            for ID in categoryIDs:
                session.run("CREATE (:Category {string_id:$ID})", ID = ID)

    def writeSynthCats(self, synthCatIDs):
        """Writes the synthesis categories to the database

        Args:
            synthCatIDs (list of str): list of synthesis category ids 
        """
        with self.driver.session() as session:
            for ID in synthCatIDs:
                session.run("CREATE (:SynthCat {string_id:$ID})", ID = ID)

    #Should be split to smaller methods
    def writeItemRecipes(self, itemRecipes, itemEnums):
        """Writes the item recipes to the database

        Args:
            itemRecipes (list of Item): The items to add to the database
            itemEnums (ItemIDEnumDict): The dictionaries used to convert enums and ids
        """
        
        self.writeItems(itemRecipes)
        self.writeRecipes(itemRecipes, itemEnums)
    
    def writeItems(self, itemRecipes):
        with self.driver.session() as session:
            for item in itemRecipes:
                #Create item
                session.run("CREATE (:Item {string_id:$ID})", ID = item.stringID)

                # #Add categories
                for category in item.categories:
                    session.run("MATCH (item:Item {string_id:$itemID}), (cat:Category {string_id:$catID}) "
                    "CREATE (item)-[:CATEGORISED_BY]->(cat)"
                    , itemID = item.stringID, catID = category)

    def writeRecipes(self, itemRecipes, itemEnums):
        with self.driver.session() as session:
            for item in itemRecipes:
                if item.recipe != None:
                    #Connect synthesis category
                    synthCatEnum = item.itemType
                    if synthCatEnum == "ITEM_KIND_FIELD": #Replacing the gathering item tag with the synthesis tag since it is functionally the same
                        synthCatEnum = "ITEM_KIND_MIX"
                    session.run("MATCH (item:Item {string_id:$itemID}),(synthCat:SynthCat {string_id:$synthCatID}) "
                    "CREATE (item)-[:SYNTH_CATEGORISED_BY]->(synthCat)"
                    , itemID = item.stringID, synthCatID = itemEnums.enumToID[synthCatEnum])

                    #Create nodes
                    def createNodeID(item, nodeNo):
                        return "R" + str(nodeNo) + "_" + item.stringID
                    createNode = ""
                    matching = ("MATCH (origin:Item {{string_id:'{0}'}}), "
                                "(e0:Element {{element_id:0}}), "
                                "(e1:Element {{element_id:1}}), "
                                "(e2:Element {{element_id:2}}), "
                                "(e3:Element {{element_id:3}}) ").format(item.stringID)
                    createRelationship = "CREATE (origin)-[:HAS_RECIPE]->({0}) ".format(createNodeID(item, 0))
                    usedItems = set()
                    for nodeNo, recipeNode in item.recipe.nodes.items():
                        if recipeNode.itemUsed != None:
                            thisNodeID = createNodeID(item, nodeNo)
                            
                            createNode += "CREATE ({0}:RecipeNode {{node_id:'{0}'}}) ".format(thisNodeID)
                        
                            #Adding what item the node needs
                            if recipeNode.itemUsed not in usedItems:
                                usedItems.add(recipeNode.itemUsed)
                                matching += "MATCH ({0} {{string_id:'{1}'}}) ".format(recipeNode.itemUsed, itemEnums.enumToID[recipeNode.itemUsed])
                            createRelationship += "CREATE ({0})-[:NEEDS]->({1}) ".format(thisNodeID, recipeNode.itemUsed)

                            #Adds the elements needed to unlock
                            if recipeNode.unlock != None:
                                createRelationship += "CREATE ({0})-[:UNLOCK_REQUIRES {{cost:{1}}}]->(e{2}) ".format(thisNodeID, recipeNode.unlock.cost, recipeNode.unlock.element)

                            #Connects the nodes to each other
                            for child in recipeNode.children:
                                createRelationship += "CREATE ({0})-[:CONNECTS_TO]->({1}) ".format(thisNodeID, createNodeID(item, child))
                            
                            #Adds the category the node unlocks
                            for synthBoost in recipeNode.synthBoosts:
                                if synthBoost.name in itemEnums.addCat:
                                    matching += "MATCH ({0}:Category {{string_id:'{1}'}}) ".format(synthBoost.name, itemEnums.addCat[synthBoost.name])
                                    createRelationship += "CREATE ({0})-[:ADDS_CAT]->({1}) ".format(thisNodeID, synthBoost.name)
                                    # createRelationship += "CREATE ({0})-[:ADD_CAT_REQUIRES"
                                else:
                                    break
                    session.run(matching + createNode + createRelationship)
                    print("Added",item.recipe.meta.recipeName)

    def clearDB(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def createDB(self, itemRecipes, itemEnumDict):
        self.clearDB()
        
        self.writeElements()
        categoryIDs = [string_id for enum, string_id in itemEnumDict.enumToID.items() if enum.startswith("ITEM_CATEGORY")]
        self.writeCats(categoryIDs)
        unusedSynthCats = ["ITEM_KIND_EXPENDABLE", "ITEM_KIND_MATERIAL", "ITEM_KIND_CORE", "ITEM_KIND_SUPPORT", "ITEM_KIND_BOOK", "ITEM_KIND_FIELD"]
        synthCatIDs =  [string_id for enum, string_id in itemEnumDict.enumToID.items() if enum.startswith("ITEM_KIND_") and enum not in unusedSynthCats]
        self.writeSynthCats(synthCatIDs)

        self.writeItemRecipes(itemRecipes, itemEnumDict)

    def applyTranslation(self, stringIDToLang, language):
        with self.driver.session() as session:
            result = session.run("MATCH (n) WHERE EXISTS (n.string_id) RETURN n.string_id")
            stringIDs = result.value()

            addLangQuery = "MATCH (n {{string_id:$ID}}) SET n.{0}_name = $name".format(language)
            for stringID in stringIDs:
                if stringID in stringIDToLang:
                    session.run(addLangQuery, ID = stringID, name = stringIDToLang[stringID])
                else:
                    print("String id", stringID, "is missing from the dictionary")
            

if __name__ == "__main__":
    ryzaDB = RyzaDB("bolt://35.174.211.189:33708", "neo4j", "flare-tools-ovens")

    itemrecipedata = "data/itemrecipedata.xml"
    mixfielddata = "data/mixfielddata.xml"
    itemCategoriesID = "data/itemdata_no.xml"
    dictPath = "data/ryza_enums_id.csv"

    itemRecipes = ItemRecipe.createItemRecipe(itemrecipedata, mixfielddata, itemCategoriesID)
    itemEnumDict = ItemIDEnumDict.createItemIDEnumDict(dictPath)
    ryzaDB.createDB(itemRecipes, itemEnumDict)

    allStringPath = "data/strcombineall.xml"

    stringIDToLang = StringIDToLang.createStringIDToLang(allStringPath)
    ryzaDB.applyTranslation(stringIDToLang, "eng")
    

    