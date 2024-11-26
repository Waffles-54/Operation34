################################################################
# OP34: Special Operations                                     #
# Program Written by Alice Griffith                            #
# Follow local laws and websites rules when using this scraper #
################################################################


####################################################################################################
# Setup Phase: Import Libraries and setup global standards                                         # 
####################################################################################################
import os
import subprocess
import sys

BASE_PATH = "internal"                                          # Root directory for databases
QUERIES = os.path.join(BASE_PATH, "query.db")                   # Database for managing internal query managment
BLACKLIST = os.path.join(BASE_PATH, "blacklist.db")             # Database for universal blacklist applications (Booru's only)
BATCHFILE = os.path.join(BASE_PATH, "batch_load.txt")  
LOGS = os.path.join(BASE_PATH, "logs.txt")                      # Log file for program failure, used in debugging [#TODO Not implemented]
DOWNLOAD_ARCHIVES = os.path.join(BASE_PATH, "downloaded.db")    # Database achrive of downloaded files to avoid redownloading

GLOBAL_BLACKLIST = []               # Internal structure for managing the globally applied blacklist (Booru's only)
GLOBAL_MODULES = []                 # Internal structure for maintaining modules to maintain information about quieries



####################################################################################################
# Scraper class: related to mechanisms of database managment, query building, and query execution  #
####################################################################################################
class Scraper:
    # Module class: represents a module to track a queries metadata
    class Module:
        # Module initalizer, sets up metadata for a query from either the database or user input @ runtime
        def __init__(self, engine, query, lid, lob, rating, mode):
            self.engine = engine        # Engine used to execute the query
            self.query = query          # the query to be executed (TAG)
            self.lid = lid              # last id of image downloaded, used in automating fresh downloads (Booru's)
            self.lob = lob              # Local blacklisted tags
            self.rating = rating        # Query image safety rating classification
            self.mode = mode            # What type of query is being executed (Tag, User, etc.)
            self.generated_query = ""   # Query for execution (built from the rest of the modules metadata)
            GLOBAL_MODULES.append(self)
        
        @staticmethod
        def add_module():
            isMoreModules, isVaildInput = True, False
            response, engine, query, lob, rating, lid, mode = [None] * 7

            while (isMoreModules): # While the user wants to add more entries
                while (isVaildInput == False):
                    print("\nEnter engine # to use:")
                    print("[1] Booru")
                    print("[2] Pixiv")
                    print("[3] Deviantart [NOT IMPLEMENTED YET]")
                    print("[4] Manual mode (direct query entry) [NOT IMPLEMENTED YET]")
                    print("[0] Exit Entry mode")
                    response = input("#: ")
                    sys.stdout.flush()
                    isVaildInput = True
                    if response == '0':
                        print("Exiting input mode...")
                        isMoreModules = False
                        break
                    elif response == '1': # Booru
                        engine = "BRU"
                    elif response == '2': # Pixiv input mode
                        engine = "PXV"
                    elif response == '3': # Manual Mode
                        engine = "OTH"
                    else:
                        isVaildInput = False

                # Execute further steps based on the engine selected
                if engine == "BRU":
                    print("\nInput search query (Do not input blacklist identifiers, currently supports 1 query):")
                    query = input("> ")
                    sys.stdout.flush()
                    isVaildInput = False

                    while (isVaildInput == False):
                        # Determine image rating classification
                        print("\nInput Rating # Classification:")
                        print("[1] Safe")
                        print("[2] Sensitive")
                        print("[3] Explicit")
                        isVaildInput = True
                        response = input("#: ")
                        if response == '1': # Safe
                            rating = "SFE"
                        elif response == '2': # Sensitive
                            rating = "SEN"
                        elif response == '3': # Explicit
                            rating = "EXP"
                        else:
                            isVaildInput = False
                        sys.stdout.flush()
                    
                    if(Scraper.Module.duplicateModuleChecker(engine, query, rating)):
                        print("Module already in database, skipping...")
                    else:
                        print("\nInput Local blacklists seperated by a space (Press enter for None):")
                        lob = input()
                        sys.stdout.flush()
                        print("\nEnter the BOORU's Last ID (LID) to download from, or Enter to skip [QUERIES TRANSSFER MODE]")
                        try:
                            response = int(input())
                            lid = response
                        except:
                            lid = 0
                        mode = "TAG"
                        print("\nGenerating query...")
                        Scraper.Module(engine, query, lid, lob, rating, mode)
                        Scraper.Module.save_module(engine, query, lid, lob, rating, mode, 'a')
                elif engine == "PXV":
                    isVaildInput = False
                    print("\nInput qwery mode:")
                    print("[1] User ID")
                    print("[2] Tag Search")
                    while(isVaildInput == False):
                        isVaildInput = True
                        response = input("#: ")
                        if response == '1': # User input mode
                            mode = "USR"
                            print("\nInput Users ID's to track (seperate by spaces):")
                            query = input().split(' ')
                            
                        elif response == '2': # Tag Search mode
                            mode = "TAG"
                            print("\nInput Tags:")
                            query = input()
                        else:
                            isVaildInput = False

                    print("\nGenerating queries...")
                    for entry in query:
                        if entry != '':
                            if(Scraper.Module.duplicateModuleChecker(engine, query, rating)):
                                print("Module already in database, skipping...")
                            else:
                                Scraper.Module(engine, entry, lid, lob, rating, mode)
                                Scraper.Module.save_module(engine, query, lid, lob, rating, mode, 'a')

                isVaildInput = False

        @staticmethod
        def add_module_from_query(response):
            engine, query, lob, rating, lid, mode = [""] * 6
            components = response.split("/")
            engine = components[2].split(".")[-2]
            if (engine == "pixiv"):
                engine = "PXV"
                mode = components[4]
                if (mode == "users"):
                    mode = "USR"
                    query = components[5]
                elif (mode == "tags"):
                    mode = "TAG"
                    query = components[5]
                if(Scraper.Module.duplicateModuleChecker(engine, query, rating)):
                    print("Module already in database, skipping...")
                else:
                    Scraper.Module(engine, query, lid, lob, rating, mode)
                    Scraper.Module.save_module(engine, query, lid, lob, rating, mode, 'a')
                    print()
            elif (engine == "gelbooru"):
                engine = "BRU"
                query = components[3].split("tags=")[1].split("+")[-1]
                if(Scraper.Module.duplicateModuleChecker(engine, query, rating)):
                    print("Module already in database, skipping...")
                else:
                    Scraper.Module(engine, query, lid, lob, rating, mode)
                    Scraper.Module.save_module(engine, query, lid, lob, rating, mode, 'a')


        @staticmethod
        def duplicateModuleChecker(engine, query, rating):
            for entry in GLOBAL_MODULES:
                if (query == entry.query) and (engine == entry.engine) and (rating == entry.rating):
                    return True
            return False
        
        @staticmethod
        def save_module(engine, query, lid, lob, rating, mode, IO):
            with open(QUERIES, IO) as file:
                db_enc = ""
                if engine == "BRU":
                    db_enc += "BRU|"
                    db_enc += query + "|"
                    db_enc += str(lid) + "|"
                    for entry in lob.split(" "):
                        if entry != '':
                            db_enc += entry + " "
                    db_enc += "|"
                    if rating == "SFE":
                        db_enc += "SFE|"
                    elif rating == "SEN":
                        db_enc += "SEN|"
                    elif rating == "EXP":
                        db_enc += "EXP|"
                elif engine == "PXV":
                    db_enc += "PXV|" + str(query) + "||||"
                elif engine == "OTH":
                    db_enc += engine
                db_enc += mode + "@"
                file.write(db_enc)

    @staticmethod
    def loadDatabases():
        # Load entries into modules
        try:
            # Load the QUERIES database into the program and proccess them, notify user if no query database exist
            with open(QUERIES, 'r') as file:
                contents = file.read()
            queries = contents.split('@')
            for query in queries:
                if query == '':
                    break
                fragments = query.split('|')
                # TODO (Waffles) Implement valid fragment testing here
                Scraper.Module(*fragments) # Generate modules from the tokenized database entries
        except:
            print("No database file exists, please run -a to add queries to the query database")

        # Load and initialize the global blacklist, notify user if no entries exist
        try:
            with open(BLACKLIST, 'r') as file:
                contents = file.read().split("|")
            for element in contents:
                if element != '':
                    GLOBAL_BLACKLIST.append(element)
        except:
            print("No blacklist database file exists, please run -b to add tags to the global blacklist database")

    @staticmethod
    def generate_queries():
            for module in GLOBAL_MODULES:
                # Build the queries from the modules metadata
                query = ""
                if module.engine == "BRU":
                    query += "https://gelbooru.com/index.php?page=post&s=list&tags="
                    query += module.query
                    query += "+id:>" + str(module.lid)
                    if module.rating == "SFE":
                        query += "+rating:general"
                    if module.rating == "SEN":
                        query += "+rating:questionable"
                    if module.rating == "EXP":
                        if module.engine == "BRU":
                            query += "+rating:explicit" 
                    for entry in GLOBAL_BLACKLIST + module.lob.split(" "):
                        if entry != '':
                            query += "+-" + entry
                elif module.engine == "PXV":
                    if module.mode == "TAG":
                        query += "https://www.pixiv.net/en/tags/"
                    elif module.mode == "USR":
                        query += "https://www.pixiv.net/en/users/"
                    query += module.query + "/"
                elif module.engine == "OTH":
                    query += module.engine
                module.generated_query = query

    @staticmethod
    def execute_queries():
        for module in GLOBAL_MODULES:
            # Execute Query & log output
            print("Downloading: \n" + module.generated_query)
            try:
                resCapture = subprocess.run(["gallery-dl", "--download-archive", DOWNLOAD_ARCHIVES, module.generated_query], capture_output=True, text=True)
                if resCapture.stdout != "":
                    # print(resCapture.stdout.splitlines()[0].split('id:>')[1].split('_')[0].split(" ")[0])
                    with open(DOWNLOAD_ARCHIVES, 'a') as file:
                        # Send output to download archives
                        file.write(resCapture.stdout)
                    # Gets the token for BRU storage
                    lid_token = resCapture.stdout.splitlines()[0].split('_')[-2] if resCapture.stdout else None
                    if (module.engine == "BRU" and lid_token != None):
                        print(lid_token)
                        module.lid = lid_token
                print("Execution Completed\n")
            except:
                print("Error: Failed to execute query\n")

    @staticmethod
    def save_queries():
        for m in GLOBAL_MODULES:
            Scraper.Module.save_module(m.engine, m.query, m.lid, m.lob, m.rating, m.mode, 'w')

    @staticmethod
    def duplicateBlacklistChecker(query):
        for entry in GLOBAL_BLACKLIST:
            if (query == entry):
                return True
        return False

# Program entry point
def main():

    # Setup Step
    if not os.path.exists("internal"):
        os.makedirs("internal")
    Scraper.loadDatabases()

    with open(BATCHFILE, 'a+') as file:
        file.seek(0)
        contents = file.read()
    for query in contents.splitlines():
        Scraper.Module.add_module_from_query(query)
    isExecuting = True

    # Automatic execution when called from a schedular
    if (len(sys.argv) == 2):
        if sys.argv[1] == "-e":
            Scraper.generate_queries()
            Scraper.execute_queries()
            Scraper.save_queries()
            isExecuting = False

    # Promting Stage
    while(isExecuting):
        print("Enter Command:")
        print("[e] execute bot")
        print("[a] add to database")
        print("[b] add to global blacklist (Booru's only)")
        print("[q] to quit")
        query = input()
        if query == "e":
            print("Execuitng database queries, this may take a while...")
            Scraper.generate_queries()
            Scraper.execute_queries()
            Scraper.save_queries()
        elif query == "a":
                Scraper.Module.add_module()
        elif query == "b":
            print("Enter globaly applied blacklisted tags to be added to the database (seperate with spaces):")
            response = input()
            tokens = response.split(' ')
            with open(BLACKLIST, 'a') as file:
                for token in tokens:
                    if (Scraper.duplicateBlacklistChecker(token) == False):
                        file.write(token + "|")
                    else:
                        print(token + " is already registered to the global blacklist")
        elif query == "q":
            print("shutting down...")
            isExecuting = False
    
if __name__ == "__main__":  main()

####################################################################################################
# Developers TODO:
# Setup an installer script
# Removal system
# viewing system
# Add image ratings to pixiv search, ?mode=r18
# Initial first run configuration function
# Make script opperatable from UNIX scheduler (crontab)
# Make engines more configurable (gelbooru, safebooru, danbooru, etc)
# Add an engine for deviantart
# Implement video scraping (Tall order, low priority)
# Implement file link batch proccessing (internal/load) or something
# Add a confirm entry for db entries
####################################################################################################