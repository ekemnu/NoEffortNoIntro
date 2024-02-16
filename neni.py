#####   No Effort No-Intro
#####	John Loreth
#####	2024
#####	v0.2
#####
#####   Process and extracts No-Intro Rom Archives, sorts by region into sub directories
#####
#####   Version history:
#####		0.1  Basic bash script
#####       0.2  Rewritten in Python
#####       0.3  Improved Tag Scraping Logic
#####       0.4  

import re
import os
#import os.path
#import shutil
import subprocess
import sys
from itertools import chain 
import argparse

# Gets the arguments passed to the script from bash
parser = argparse.ArgumentParser( description='Processes a given No-Intro archive, sorts by region into sub directories',
                    epilog='Written by John Loreth 2024')
parser.add_argument('zipFile')
parser.add_argument('-d', '--dry-run', const='echo', default='unzip',
                    action='store_const', dest='unzipCMD',
                    help='Runs the script without making any changes')
parser.add_argument('-r', '--release', nargs=1,
                    action='store', dest='relVers',
                    help='Specify No-Intro release information to include after processing')
flags = parser.parse_args()

print("DEBUG: flags is", flags, "type is", type(flags))          
print("DEBUG: flags.zipFie is", flags.zipFile, "type is", type(flags.zipFile))
print("DEBUG: sys.argv is", sys.argv, "type is", type(sys.argv))

global zipFile
global scriptFn
scriptFn = sys.argv[0]
try:
    os.path.isdir(flags.zipFile)                                 # Checks to see if script was called without arguments
except Exception:                               # If the script was run without arguments
    print("Error: Must specify a file")
    print("       Run the script again supplying a valid path to a No-Intro rom archive")
    print("         Ex: $", scriptFn, "/home/user/Downloads/archive.zip")
    quit(1)
else:                                           # If the script was run with arguments
    print("DEBUG: sys.argv[1:] is ", sys.argv[1:], "type is ", type(sys.argv[1:]))
    zipFile = os.path.abspath(flags.zipFile)
    print("DEBUG: zipFile is", zipFile, type(zipFile))

# Checks if target file is a zip file
def checkZip():
    global zipFile
    global zipPath
    global zipFn
    global zipFnRoot
    global zipFnExt
    
    try:
        os.path.isfile(zipFile)             # Checks if target file exsists
    except Exception:                           # Error if the file does not exsist
        print("Error: Target File Cannot Be Found")
        print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
        print("         Ex: $", scriptFn, "/home/user/Downloads/archive.zip")
        quit(1)
    else:                                       # If the file exsists
        zipPath, zipFn = os.path.split(zipFile)
        zipFnRoot, zipFnExt = os.path.splitext(zipFn)
        print("DEBUG: zipPath is:", zipPath, type(zipPath), "zipFn is:", zipFn, type(zipFn), "zipFnRoot is:", zipFnRoot, type(zipFnRoot), "zipFnExt is:", zipFnExt, type(zipFnExt))
        if ".zip" not in zipFnExt:
            print("Error: Target File is no a Zip Archive")
            print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
            print("         Ex: $", scriptFn, "/home/user/Downloads/archive.zip")
            quit(1)
        else:
            print("DEBUG: entered else")
    		
def unzip():
        global extPath
        
        # STILL NEED TO CHECK IF EXT PATH IS THERE
        
        print("DEBUG: entered unzip")
        extPath = os.path.join(zipPath, zipFnRoot)
        bashCMD = flags.unzipCMD, '-d', '\'' + extPath + '\'', '\'' + zipFile + '\''
        #bashCMD = 'echo -d', extPath, zipFile
        print("DEBUG: extPath is", extPath, type(extPath))
        execBash(' '.join(bashCMD))
        if bash.returncode == 0:
            print(scriptFn, ": Sucessfully decompressed archive to", extPath)
        else:
            print("Error: Archive Decompression Failed\n", bash.stderr)
            quit(1)
            
def processRom():
    global romRegion
    global romLang
    global rom
    global eurPath
    global jpnPath
    global worPath
    global usaPath
    global regions
    
    romRegion = {
            "USA": ( "USA", "Canada" ),
            "Japan": ( "Japan", "null" ),
            "Europe": ( "Europe", "Australia", "PAL", "United Kingdom" ),
            "EurWor": ( "Germany", "France", "Spain", "Italy", "Netherlands", "Sweden", "Scandinavia", "Denmark" ),
            "World": ( "World", "Asia", "China", "Brazil", "Taiwan", "Korea", "Russia", "Hong Kong", "Argentina", "Latin America", "Mexico" )
    }
    romLang = ( "En", "Fr", "De", "Es", "It", "Nl", "Ja", "Sv", "Pt", "No","Da", "Zh", "Fi", "PT-BR", "Pl", "Ru", "Ko", "Ar", "Ca", "Zh-Hans", 
                "Zh-Hant", "En-US", "Pt-PT", "En-GB", "Hu", "El", "Es-MX", "Es-XL", "Kw", "Ro", "Ro", "Yi", )
    regions = list(chain(*romRegion.values()))    
    
    def makeDirs():
        eurPath = extPath + "/Europe"
        jpnPath = extPath + "/Japan"
        worPath = extPath + "/World"
        usaPath = extPath + "/USA"

        if os.path.isdir(eurPath):
            pass
        else:
            print("DEBUG: entered mkdir eur", eurPath)
            os.mkdir(eurPath)
        if os.path.isdir(jpnPath):
            pass
        else: 
            print("DEBUG: entered mkdir jpn", jpnPath)
            os.mkdir(jpnPath)
        if os.path.isdir(worPath):
            pass
        else: 
            print("DEBUG: entered mkdir wor", worPath)
            os.mkdir(worPath)
            
        if os.path.isdir(usaPath):
            pass
        else: 
            print("DEBUG: entered mkdir usa", usaPath)
            os.mkdir(usaPath)
        
        search string in reverse for ) to get index for each )
        search string in reverse for ( to get index for each (
        count indexes for ( and for ) and see if they are equal
        if they are equal, move forward, if not they need more processing to figure out which close corresponds to which open
        once we have matching set of ( ) we can split whats in between -- can python automatically split between chatacters?
        if they are odd we need to compare the numbers for example: ( at 0,10,20,30  and ) at 15,25,35. looking for a ) in between each (
                                                                            15,25,35 since there is no ) betwen 0 and 10, we can infer that
                                                                                its not a tag; check from L>R more likely to find on L side
    def gatherTags(rom):    # Scraps tags from Rom file name
        regionTags = []     # Create empty list for region tags
        languageTags = []   # Create empty list for language tags
        miscTags = []       # Create empty list for misc tags
        print("DEBUG: regions is:", regions, type(regions)) 
        tagsCollected = re.findall(r'\((.*?)\)', rom)   # Scrape file name for all occurrences of (***)
        for tag in tagsCollected:                       # For each of the collected tags
            tagSplit = tag.split(',')                   # Split the tags on commas
            for splitTag in tagSplit:                   # For each of the individual tags
                splitTag = splitTag.strip()             # Strip whitespace
                if "+" in splitTag:
                    splitTag = splitTag.split('+')
                    print("DEBUG: splittag after split:", splitTag, type(splitTag))             # Maybe try to read the file name in reverse to avoid unclosed errors
                    tagSplit.extend(splitTag)
                    continue
                else:
                    print("DEBUG: splitTag is:", splitTag, type(splitTag))
                    if splitTag in regions:                 # If the tag can be found in the regions list
                        regionTags.append(splitTag)         # Add it to the regionTags list
                        auditLogAddTags("regionTags", splitTag)
                    elif splitTag in romLang:               # If the tag can be found in the Language list
                        languageTags.append(splitTag)       # Add it to the languageTags list
                        auditLogAddTags("languageTags", splitTag)
                    else:                                   # Else if the tag cannot be matched
                        miscTags.append(splitTag)           # Add it to the miscTags list
                        auditLogAddTags("miscTags", splitTag)
        print("DEBUG: regionTags is:", regionTags, type(regionTags))
        tags = { "regionTags" : regionTags, "languageTags" : languageTags, "miscTags" : miscTags } # Save scarped tag info to dictionary
        return tags
            
    def moveRom(rom, tags):
        usaPath = extPath + "/USA"
        eurPath = extPath + "/Europe"
        jpnPath = extPath + "/Japan"
        worPath = extPath + "/World"
        #print("DEBUG: eurPath is", eurPath, type(eurPath), "jpnPath is", jpnPath, type(jpnPath), "worPath is", worPath, type(worPath),  )
    
        # Match by region  
        if tags["regionTags"]:                                          # If regionTags dictionary entry is not empty
            for tag in tags["regionTags"]:
                if "USA" in tags["regionTags"]:                             # Attempt to bail out early by matching on master sort region
                    os.replace(extPath + "/" + rom, usaPath + "/" + rom)
                    auditLogAddLn("USA", rom)
                    print("DEBUG: *** Moved rom to", usaPath, " ***")
                    return 0
                elif tag == "Japan":
                    print("DEBUG: len(tags[regionTags]) is:", len(tags["regionTags"]), type(len(tags["regionTags"])))
                    if len(tags["regionTags"]) == 1:
                        os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                        auditLogAddLn("Japan", rom)
                        print("DEBUG: *** Moved rom to", jpnPath, " ***")
                        return 0
                    elif tags["regionTags"][1] in romRegion.keys(): 
                        if len(tags["languageTags"]) >= 1 and tags["languageTags"][0] != "Ja":
                            continue
                        else:
                            os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                            auditLogAddLn("Japan", rom)
                            print("DEBUG: *** Moved rom to", jpnPath, " ***")
                            return 0
                    else:
                        os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                        auditLogAddLn("Japan", rom)
                        print("DEBUG: *** Moved rom to", jpnPath, " ***")
                        return 0
                elif tag == "Europe":
                    os.replace(extPath + "/" + rom, eurPath + "/" + rom)
                    auditLogAddLn("Europe", rom)
                    print("DEBUG: *** Moved rom to", eurPath, " ***")
                    return 0
                elif tag == "World":
                    if not tags["languageTags"] or "En" in tags["languageTags"]:
                        os.replace(extPath + "/" + rom, usaPath + "/" + rom)
                        auditLogAddLn("USA", rom)
                        print("DEBUG: *** Moved rom to", usaPath, " ***")
                        return 0
                    else:
                        os.replace(extPath + "/" + rom, worPath + "/" + rom)
                        auditLogAddLn("World", rom)
                        print("DEBUG: *** Moved rom to", worPath, " ***")
                        return 0
                # We werent able to bail out
                if tag in romRegion["USA"]:
                    if not tags["languageTags"] or "En" in tags["languageTags"]:
                        os.replace(extPath + "/" + rom, usaPath + "/" + rom)
                        auditLogAddLn("USA", rom)
                        print("DEBUG: *** Moved rom to", usaPath, "folder ***")
                        return 0
                    else:
                        os.replace(extPath + "/" + rom, worPath + "/" + rom)
                        auditLogAddLn("World", rom)
                        print("DEBUG: *** Moved rom to", worPath, " ***")
                        return 0
                elif tag in romRegion["Japan"]:
                        os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                        auditLogAddLn("Japan", rom)
                        print("DEBUG: *** Moved rom to", jpnPath, " ***")
                        return 0
                elif tag in romRegion["Europe"]:
                    os.replace(extPath + "/" + rom, eurPath + "/" + rom)
                    auditLogAddLn("Europe", rom)
                    print("DEBUG: *** Moved rom to", eurPath, " ***")
                    return 0
                elif tag in romRegion["World"]:
                    os.replace(extPath + "/" + rom, worPath + "/" + rom)
                    auditLogAddLn("World", rom)
                    print("DEBUG: *** Moved rom to", worPath, " ***")
                    return 0
                elif tag in romRegion["EurWor"]:
                    if "En" in tags["languageTags"]:
                        os.replace(extPath + "/" + rom, eurPath + "/" + rom)
                        auditLogAddLn("Europe", rom)
                        print("DEBUG: *** Moved rom to", eurPath, " ***")
                        return 0
                    else:
                        os.replace(extPath + "/" + rom, worPath + "/" + rom)
                        auditLogAddLn("World", rom)
                        print("DEBUG: *** Moved rom to", worPath, " ***")
                        return 0
                else:
                    continue
        elif tags["languageTags"]:
            if "En" in tags["languageTags"]:
                auditLogAddLn("USA", rom)
                ("DEBUG: *** REGIONLESS En ROM LEFT IN ROOT ***")
                return 0
            elif "Ja" in tags["languageTags"]:
                os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                auditLogAddLn("Japan", rom)
                print("DEBUG: *** REGIONLESS Jp ROM MOVED TO", jpnPath, " ***")
                return 0
            else:
                os.replace(extPath + "/" + rom, worPath + "/" + rom)
                auditLogAddLn("World", rom)
                print("DEBUG: *** REGIONLESS ROM WITH Lng MOVED TO", worPath, " ***")
                return 0
        else:
            ("DEBUG: *** UNMATCHED ROM LEFT IN ROOT ***")
            return 1

    print("DEBUG: romRegion USA is", romRegion["USA"], type(romRegion["USA"]))
    print("DEBUG: romRegion[Japan] is", romRegion["Japan"], type(romRegion["Japan"]))
    print("DEBUG: romRegion[Europe] is", romRegion["Europe"], type(romRegion["Europe"]))
    print("DEBUG: romRegion[EurWor] is", romRegion["EurWor"], type(romRegion["EurWor"]))
    print("DEBUG: romRegion[World] is", romRegion["World"], type(romRegion["World"]))
    print("DEBUG: romLang is", romLang, type(romLang))
    
    makeDirs()

    for rom in os.listdir(extPath):                                         # For each of the Rom Files in the extraction path
        print("DEBUG: WORKING ON ROM", rom, type(rom))
        if rom.endswith(".zip") and '[BIOS]' not in rom:                    # If the file is a archive, and is not a bios
            tags = gatherTags(rom)                                          # Scrape rom name for tags to process
            print("DEBUG: tags are:", tags, type(tags))
            results = moveRom(rom, tags)                                    # Process tags and move roms into folders
            print("DEBUG: results of romMove is", results, type(results))
            if results != 0:
                auditLogAddLn("UnKwn", rom)
                print("DEBUG: *** Left in root folder ***")
        else:
            continue
        
# Maintains a log of actions performed by the script
def auditLog():
    global auditLogAddTags  # Global sub-function to add tags to tag buffer
    global auditLogAddLn    # Global sub-function to add lines to log buffer
    global auditLogWrite    # Global sub-function to write the log buffer to file
    
    # Adds a line to the logline buffer sort catagory
    def auditLogAddLn(auditLogGrp, auditLogLine):
        auditLogBuffer[auditLogGrp].append(auditLogLine)
    
    # Adds a tag to the collected tag buffer
    def auditLogAddTags(auditLogAddTagGrp, auditLogAddTagTag):
        auditLogTags[auditLogAddTagGrp].append(auditLogAddTagTag)
    
    # Processes audit log buffers and writes them to a file in the extraction directory
    def auditLogWrite():
        #print("DEBUG: extPath in auditLogWrite is", extPath, type(extPath))
        #print("DEBUG: auditFn is", auditFn, type(auditFn))
        #print("DEBUG: auditLogBuffer in auditLogWrite is", auditLogBuffer, type(auditLogBuffer))
        auditFPath = extPath + "/" + auditFn
        auditFile = open(auditFPath, "a")
        
        # Process the tag buffer and add it to the log buffer
        #print("DEBUG: auditLogTags is", auditLogTags, type(auditLogTags))
        for auditLogTagGrp in auditLogTags.keys():
            #print("DEBUG: auditLogTagGrp is", auditLogTagGrp, type(auditLogTagGrp))
            if auditLogTags[auditLogTagGrp]:
                #print("DEBUG: Entered auditLogTags if")
                auditLogBuffer["ColTag"].append(auditLogTagGrp.upper() + ":")
                # Deduplicate and sort the tag collection
                auditLogTagsSort = list(set(auditLogTags[auditLogTagGrp]))
                auditLogTagsSort.sort()
                #print("DEBUG: auditLogTagsSort is", auditLogTagsSort, type(auditLogTagsSort))
                for auditLogTagTag in auditLogTagsSort:
                    #print("DEBUG: auditLogTagTag is", auditLogTagTag, type(auditLogTagTag))
                    # Count occurances of tag in tag collection
                    auditLogTagCnt = auditLogTags[auditLogTagGrp].count(auditLogTagTag)
                    #print("DEBUG: auditLogTagCnt is", auditLogTagCnt, type(auditLogTagCnt))
                    #Append tag to ColTag buffer
                    auditLogBuffer["ColTag"].append(auditLogTagTag + " " + str(auditLogTagCnt))
            else:
                #print("DEBUG: Entered auditLogTags continue")
                continue
            auditLogBuffer["ColTag"].append("")
        
        # Process the log buffer and write it to disk
        for auditLogGrp in auditLogBuffer.keys():
            #print("DEBUG: auditLogGrp is", auditLogGrp, type(auditLogGrp))
            for auditLogLn in auditLogBuffer[auditLogGrp]:
                #print("DEBUG: auditLogLn is", auditLogLn, type(auditLogLn))
                auditFile.write(auditLogLn + '\n')
        
        auditFile.close()
    
    auditLogTags = { "regionTags" : [], "languageTags" : [], "miscTags" : [] }
    auditLogBuffer = {
        "ColTag": [ "### Tags That Were Scraped From File Names ###" ],
        "USA": [ "### Files That Matched the USA Region ###" ],
        "Japan": [ "\n### Files That Matched the Japan Region ###" ],
        "Europe": [ "\n### Files That Matched a European Region ###" ],
        "World": [ "\n### Files That Matched a World Region ###" ],
        "UnKwn": [ "\n### Files That Were unmatched ###" ]
    }
    
    # Determine what the audit log file will be named
    if flags.relVers:
        print("DEBUG: flags.relVers is", ' '.join(flags.relVers), type(' '.join(flags.relVers)))
        auditFn = "[ " + ' '.join(flags.relVers) + " No-Intro Set ]"
    else:
        auditFn = "[ " + zipFn + " No-Intro Set ]"
    
# BASH ENGINE: Runs commands in a bash shell
def execBash(execBash_CMD):
    global bash
    
    print("DEBUG: execbash bashCMD is", execBash_CMD)
    bash=subprocess.run(execBash_CMD, shell = True, executable = "/bin/bash", capture_output=True)
    print("DEBUG: execbash bash is", bash, type(bash))

# Defines the order subroutines are executed
def mainRoutine():
    auditLog()              # Creates and manages a log file
    checkZip()              # Performs sanity checks on target file
    unzip()                 # Unzips target file
    processRom()            # Processes roms based on region and language and moves them into sub-folders
    auditLogWrite()         # Writes log buffer to file
    exit(0)
	
# Calls the main routine on script startup
mainRoutine()               # Script entry point; execution begins here
