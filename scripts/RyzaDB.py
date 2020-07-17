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
                #Create item
                session.run("CREATE (:Item {string_id:$ID})", ID = item.stringID)

                # #Add categories
                for category in item.categories:
                    session.run("MATCH (item:Item {string_id:$itemID}),(cat:Category {string_id:$catID}) "
                    "CREATE (item)-[:CATEGORISED_BY]->(cat)"
                    , itemID = item.stringID, catID = itemEnums.englishToID[category])
                
                #Add recipe
                if item.recipe != None:
                    #Connect synthesis category
                    session.run("MATCH (item:Item {string_id:$itemID}),(synthCat:SynthCat {string_id:$synthCatID}) "
                    "CREATE (item)-[:SYNTH_CATEGORISED_BY]->(synthCat)"
                    , itemID = item.stringID, synthCatID = itemEnums.enumToID[item.recipe.meta.synCategory])

                    #Create nodes
                    def createNodeID(item, nodeNo):
                        return "R" + str(nodeNo) + "_" + item.stringID
                    createNode = ""
                    matching = "MATCH (origin:Item {{string_id:{0}}}) ".format(item.stringID)
                    createRelationship = "CREATE (origin)-[:HAS_RECIPE]->(:RecipeNode {{node_id:{0}}}) ".format(createNodeID(item, 0))
                    usedItems = set()
                    for recipeNode in item.recipe.nodes:
                        if recipeNode.itemUsed != None:
                            thisNodeID = createNodeID(item, nodeNo)
                            
                            createNode += "CREATE ({0}:RecipeNode {{node_id:{0}}}) ".format(thisNodeID)
                        
                            #Adding what item the node needs
                            if recipeNode.itemUsed not in usedItems:
                                usedItems.add(recipeNode.itemUsed)
                                matching += "MATCH ({0} {{string_id:{1}}}) ".format(recipeNode.itemUsed, itemEnums.enumToID[recipeNode.itemUsed])
                            createRelationship += "CREATE ({0})-[:NEEDS]->({1}) ".format(thisNodeID, recipeNode.itemUsed)

                            #Connects the nodes to each other
                            for child in recipeNode.children:
                                createRelationship += "CREATE ({0})-[:CONNECTS_TO]->({1}) ".format(thisNodeID, createNodeID(item, child))
                            
                            #Adds the category the node unlocks
                            for synthBoost in recipeNode.synthBoosts:
                                if synthBoost in itemEnums.addCat:
                                    matching += "MATCH ({0}:Category {{string_id:{1}}}) ".format(synthBoost, itemEnums.addCat[synthBoost])
                                    createRelationship += "CREATE ({0})-[:ADDS_CAT]->({1}) ".format(thisNodeID, synthBoost)
                                else:
                                    break
                    
                    session.run(matching + createNode + createRelationship)
                    
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

    