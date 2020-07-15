from neo4j import GraphDatabase
import ItemRecipe
import ItemIDEnumDict
import csv

class RyzaDB:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)

    def close(self):
        self.driver.close()
    
    def writeElements(self):
        with self.driver.session() as session:
            session.run("CREATE (:Element {element_id:0}) " #fire
                        "CREATE (:Element {element_id:1}) " #ice
                        "CREATE (:Element {element_id:2}) " #lightning
                        "CREATE (:Element {element_id:3}) ")#wind
    
    def writeCats(self, categoryIDs):
        with self.driver.session() as session:
            for ID in categoryIDs:
                session.run("CREATE (:Category {string_id:$ID})", ID = ID)

    def writeSynthCats(self, synthCatEnums):
        with self.driver.session() as session:
            for enum in synthCatEnums:
                session.run("CREATE (:SynthCat {string_id:$enum})", enum = enum)

    def writeItemRecipes(self, itemRecipes, itemEnums):
        with self.driver.session() as session:
            for item in itemRecipes:
                session.run("CREATE (:Item {string_id:$ID})", ID = item.stringID)
                for category in item.categories:
                    session.run("MATCH (item:Item {string_id:$itemID}),(cat:Category {string_id:$catID}) "
                    "CREATE (item)-[:CATEGORISED_BY]->(cat)"
                    , itemID = item.stringID, catID = itemEnums.englishToID[category])
                
                if item.recipe != None:
                    session.run("MATCH (item:Item {string_id:$itemID}),(synthCat:SynthCat {string_id:$synthCatID}) "
                    "CREATE (item)-[:SYNTH_CATEGORISED_BY]->(synthCat)"
                    , itemID = item.stringID, synthCatID = item.recipe.meta.synCategory)

                    nodeNo = 0
                    createNode = ""
                    createRelationship = ""
                    def createNodeID(item, nodeNo):
                        return "R" + str(nodeNo) + "_" + item.stringID
                    for recipeNode in item.recipe:
                        if recipeNode.itemUsed != 0:
                            thisNodeID = createNodeID(item.stringID, nodeNo)
                            
                            createNode += "CREATE ({0}:RecipeNode {node_id:{0}}) ".format(thisNodeID)
                            
                            createRelationship += "MATCH (item:Item {string_id:{0}}) CREATE ({1})-[:NEEDS_ITEM]->(item)".format(
                                itemEnums.enumToID(recipeNode.itemUsed), thisNodeID)

                            for child in recipeNode.children:
                                createRelationship += "CREATE ({0})-[:CONNECTS_TO]->({1})".format(thisNodeID, createNodeID(item.stringID, child))
                            
                            for unlock in recipeNode.unlock:
                                if unlock in itemEnums.addCat:
                                    createRelationship += "MATCH (cat:Category {string_id:{0}}) CREATE ({1})-["
                                else:
                                    break;
                                    
                        nodeNo += 1
                        # if isFirstNode:
                        #     createNode += ("MATCH (item:Item {string_id:$itemID}) "
                        #     "CREATE (item)-[:HAS_RECIPE]->(:RecipeNode {node_id:$nodeID}) "
                        #     , itemID = item.stringID, nodeID = createNodeID(item.stringID, nodeNo))
                        #     isFirstNode = False
                        # else:

                    

    def clearDB(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")


    def print_greeting(self, message):
        with self.driver.session() as session:
            greeting = session.write_transaction(self._create_and_return_greeting, message)
            print(greeting)

    @staticmethod
    def _create_and_return_greeting(tx, message):
        result = tx.run("CREATE (a:Greeting) "
                        "SET a.message = $message "
                        "RETURN a.message + ', from node ' + id(a)", message=message)
        return result.single()[0]


if __name__ == "__main__":
    itemrecipedata = "data/itemrecipedata.xml"
    mixfielddata = "data/mixfielddata.xml"
    itemcat_id = "data/itemcat_id.csv"
    dictPath = "data/ryza_enums_id.csv"
    itemRecipe = ItemRecipe.createItemRecipe(itemrecipedata, mixfielddata, itemcat_id)
    
    ryzaDB = RyzaDB("bolt://localhost:7687", "neo4j", "1")
    ryzaDB.clearDB()
    ryzaDB.writeElements()

    itemEnums = ItemIDEnumDict.createItemIDEnumDict(dictPath)
    categoryIDs = [string_id for enum, string_id in itemEnums.enumToID.items() if enum.startswith("ITEM_CATEGORY")]
    ryzaDB.writeCats(categoryIDs)
    synthCatEnums =  [enum for enum, string_id in itemEnums.enumToID.items() if enum.startswith("MIX_RECIPE_CATEGORY_")]
    ryzaDB.writeSynthCats(synthCatEnums)

    itemRecipes = ItemRecipe.createItemRecipe(itemrecipedata, mixfielddata, itemcat_id)
    ryzaDB.writeItemRecipes(itemRecipes, itemEnums)
    pass

    