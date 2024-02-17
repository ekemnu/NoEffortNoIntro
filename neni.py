#####   No Effort No-Intro
#####	John Loreth
#####	2024
#####	v0.8
#####
#####   Process and extracts No-Intro Rom Archives, sorts by region into sub directories
#####
#####   Version history:
#####		0.1  Basic bash script
#####       0.2  Rewritten in Python
#####       0.3  Improved Tag Scraping Logic
#####       0.4  Functionalized rom movement
#####       0.5  Functionalized sort dir creation and create only as needed
#####       0.6  Added move buffer for --dry-run mode
#####       0.7  Rewrote audit log to use move buffer data instead of independent buffer
#####       0.8  Further design changes audit log, added a message buffer

import re
import os
import subprocess
import sys
from itertools import chain 
import argparse
from datetime import datetime

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
global exeTime
now = datetime.now()
exeTime = now.strftime("%m/%d/%Y %H:%M:%S")

print("DEBUG: now is", now, type(now))

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

def auditLog():
    global auditLogWrite    # Global sub-function to write the log buffer to file
    global auditLogAddTags
        
    # Adds a tag to the collected tag buffer
    def auditLogAddTags(auditLogAddTagGrp, auditLogAddTagTag):
        moveBuffer["ColTag"][auditLogAddTagGrp].append(auditLogAddTagTag)
    
    # Processes audit log buffers and writes them to a file in the extraction directory
    def auditLogWrite():
        auditLogTagCnted = []
        auditFPath = extPath + "/" + auditFn
        auditFile = open(auditFPath, "a")
        
        def cntRoms():
            auditRomsCnted = []
            for cntRomGrp in moveBuffer.keys():
                #print("DEBUG: entered cntRom for")
                if cntRomGrp != "ColTag":
                    #print("DEBUG: entered cntRom if not")
                    #print("DEBUG: len(moveBuffer[" + cntRomGrp +"]) is", len(moveBuffer[cntRomGrp]), type(len(moveBuffer[cntRomGrp])))
                    auditRomsCnted.append(cntRomGrp)
                    auditRomsCnted.append(len(moveBuffer[cntRomGrp]))
                    #print("DEBUG: auditRomsCnted is", auditRomsCnted, type(auditRomsCnted))
            auditRomsTotals = { grp:ttl for (grp,ttl) in zip(auditRomsCnted[::2], auditRomsCnted[1::2])}  
            auditRomsTotals["Total"] = sum(auditRomsCnted[1::2])
            #print("DEBUG: auditRomsTotals is", auditRomsTotals, type(auditRomsTotals))
            #print("DEBUG: sum is", sum(auditRomsCnted[1::2]), type(sum(auditRomsCnted[1::2])))
            print("DEBUG: auditRomsTotals is", auditRomsTotals, type(auditRomsTotals))
            return auditRomsTotals
                   
        # Process the tag buffer and add it to the log buffer
        #print("DEBUG: moveBuffer[ColTag][regionTags] is", moveBuffer["ColTag"]["regionTags"], type(moveBuffer["ColTag"]["regionTags"]))
        #print("DEBUG: moveBuffer[ColTag][languageTags] is", moveBuffer["ColTag"]["languageTags"], type(moveBuffer["ColTag"]["languageTags"]))
        #print("DEBUG: moveBuffer[ColTag][miscTags] is", moveBuffer["ColTag"]["miscTags"], type(moveBuffer["ColTag"]["miscTags"]))
        
        def cntTags():
            auditLogTagCnted = [ [], [] ]
            auditLogTagCnt = []                                                             # Create empty list to hold the counts
            for auditLogTagGrp in moveBuffer["ColTag"].keys():                              # For each of the catagories in the Collected Tags
                if moveBuffer["ColTag"][auditLogTagGrp]:                                    # If the catagory has tags
                    print("DEBUG: auditLogTagGrp is", auditLogTagGrp, type(auditLogTagGrp))
                    # Deduplicate and sort the tag collection
                    auditLogTagsSort = list(set(moveBuffer["ColTag"][auditLogTagGrp]))      # Dedpuelicate by using set, return a list
                    auditLogTagsSort.sort()                                                 # Sort the Dedupelicated list
                    auditLogTagCnted[0].append("TOTALS")                                      # Add blank space as first item for formatting
                    auditLogTagCnted[1].append(auditLogTagGrp.upper() + ":")             # Add the tag catagory in uppercase as first item
                    print("DEBUG: auditLogTagCnted[0],[1] is", auditLogTagCnted[0], type(auditLogTagCnted[1]), auditLogTagCnted[1], type(auditLogTagCnted[1]))
                    for auditLogTagTag in auditLogTagsSort:                                 # For each of the tags in the sorted list
                        # Count occurances of tag in tag collection
                        auditLogTagCnt = moveBuffer["ColTag"][auditLogTagGrp].count(auditLogTagTag)
                        # Append tag to ColTag list
                        auditLogTagCnted[0].append(str(auditLogTagCnt))
                        auditLogTagCnted[1].append(auditLogTagTag)
                else: 
                    continue
                auditLogTagCnted[0].append("")                                      # Add blank space as first item for formatting
                auditLogTagCnted[1].append("")
                #auditLogTagCnt.append(sum( ) # Sum the totals for each catagory
            print("DEBUG: auditLogTagCnted is", auditLogTagCnted, type(auditLogTagCnted))
            return auditLogTagCnted     # Return counted lists to add them to the moveBuffer
        
        moveBuffer["Totals"] = cntRoms()
        moveBuffer["ColTag"] = cntTags()
        print("DEBUG: moveBufferTotals after is", moveBuffer["Totals"], type(moveBuffer["Totals"]))
        
        # Write the audit log header information
        auditFile.write("No Effort No Intro" + '\n')
        auditFile.write("   Audit Log" + '\n\n')
        auditFile.write("Created on:    " + exeTime + '\n')
        auditFile.write("Processed:     " + flags.zipFile + '\n')
        auditFile.write("Extracted to:  " + extPath + '\n')
        auditFile.write("Total Files:   " + str(moveBuffer["Totals"]["Total"]) + '\n\n')
        
        # Process the log buffer and write it to disk
        for auditLogGrp in moveBuffer.keys():
            print("DEBUG: auditLogGrp is", auditLogGrp, type(auditLogGrp))
            if auditLogGrp == "ColTag":
                print("DEBUG: moveBuffer[auditLogGrp][0] is", moveBuffer[auditLogGrp][0], type(moveBuffer[auditLogGrp][0]))
                print("DEBUG: moveBuffer[auditLogGrp][1] is", moveBuffer[auditLogGrp][1], type(moveBuffer[auditLogGrp][1]))
                auditFile.write("### Tags That Were Scraped From File Names ###" + '\n')
                for auditLogLn in moveBuffer[auditLogGrp][1]:
                    index = int(moveBuffer[auditLogGrp][1].index(auditLogLn))
                    #print("DEBUG: index is", index, type(index))
                    #print("DEBUG: index", index, "is", str(moveBuffer[auditLogGrp][0][index]) + str(moveBuffer[auditLogGrp][1][index]))
                    auditFile.write(str(moveBuffer[auditLogGrp][0][index]).rjust(6, ' ') + " " + str(moveBuffer[auditLogGrp][1][index]) + '\n')
                    # Add blank line at end of list for formatting
                auditFile.write('\n')
                continue
            elif auditLogGrp == "UnKwn":
                auditFile.write("### Files That Were Unmatched ###" + '\n')
            else:
                if auditLogGrp != "Totals":
                    print("DEBUG: str(moveBuffer[Totals][auditLogGrp]) is", str(moveBuffer["Totals"][auditLogGrp]), type(str(moveBuffer["Totals"][auditLogGrp])))
                    auditFile.write("### " + str(moveBuffer["Totals"][auditLogGrp]) + " Files Matched the " + auditLogGrp + " Region ###" + '\n')
                #print("DEBUG: auditLogGrp is", auditLogGrp, type(auditLogGrp))
            for auditLogLn in moveBuffer[auditLogGrp]:
                #print("DEBUG: auditLogLn is", auditLogLn, type(auditLogLn))
                auditFile.write(str(auditLogLn) + '\n')
            auditFile.write('\n')
        auditFile.close()
    
    # Determine what the audit log file will be named
    if flags.relVers:
        print("DEBUG: flags.relVers is", ' '.join(flags.relVers), type(' '.join(flags.relVers)))
        auditFn = "[ " + ' '.join(flags.relVers) + " No-Intro Set ]"
    else:
        auditFn = "[ " + zipFn + " No-Intro Set ]"
    
    #auditLogTags = { "regionTags" : [], "languageTags" : [], "miscTags" : [] }

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

        extPath = os.path.join(zipPath, zipFnRoot)
        bashCMD = flags.unzipCMD, '-d', '\'' + extPath + '\'', '\'' + zipFile + '\''
        print("DEBUG: extPath is", extPath, type(extPath))
        if not os.path.isdir(extPath):
            execBash(' '.join(bashCMD))
            if bash.returncode == 0:
                print(scriptFn, ": Sucessfully decompressed archive to", extPath)
            else:
                print("Error: Archive Decompression Failed\n", bash.stderr)
                quit(1)
        else:
            if flags.unzipCMD.startswith('u'):
                print("Error: Decompression Target Directory Already Exists\n")
                quit(1)
            else:
                pass

def processRom():
    global romRegion
    global romLang
    global rom
    global eurPath
    global jpnPath
    global worPath
    global usaPath
    global regions
    global makeDir
    
    romRegion = {
            "USA": ( "USA", "Canada" ),
            "Japan": ( "Japan", "null" ),
            "Europe": ( "Europe", "Australia", "PAL", "United Kingdom", "New Zealand" ),
            "EurWor": ( "Germany", "France", "Spain", "Italy", "Netherlands", "Sweden", "Scandinavia", "Denmark" ),
            "World": ( "World", "Asia", "China", "Brazil", "Taiwan", "Korea", "Russia", "Hong Kong", "Argentina", "Latin America", "Mexico" )
    }
    romLang = ( "En", "Fr", "De", "Es", "It", "Nl", "Ja", "Sv", "Pt", "No","Da", "Zh", "Fi", "PT-BR", "Pl", "Ru", "Ko", "Ar", "Ca", "Zh-Hans", 
                "Zh-Hant", "En-US", "Pt-PT", "En-GB", "Hu", "El", "Es-MX", "Es-XL", "Kw", "Ro", "Es-ES", "Yi", "Gd", "Cs", "Sl")
    regions = list(chain(*romRegion.values()))    
    
    def makeDir(srtFolder):
        if os.path.isdir(extPath):
            if not os.path.isdir(extPath + "/" + srtFolder):
                print("DEBUG: mkdir", srtFolder)
                os.mkdir(extPath + "/" + srtFolder)
            else:
                pass
        else:
            print("DEBUG: UNABLE TO CREATE SORT DIRECTORY EXITING")
            exit(1)

    def gatherTags(rom):    # Scraps tags from Rom file name
        regionTags = []     # Create empty list for region tags
        languageTags = []   # Create empty list for language tags
        miscTags = []       # Create empty list for misc tags
        
        tagsCollected = re.findall(r'\((?=[^(]*\))(.*?)\)', rom)    # Scrape file name in reverse for all occurrences of (***) matching only complete (***)
        for tag in tagsCollected:                                   # For each of the collected tags
            tagSplit = tag.split(',')                               # Split the tags on commas
            for splitTag in tagSplit:                               # For each of the individual tags
                splitTag = splitTag.strip()                         # Strip whitespace
                if "+" in splitTag:
                    splitTag = splitTag.split('+')
                    tagSplit.extend(splitTag)
                    continue
                else:
                    if splitTag in regions:                 # If the tag can be found in the regions list
                        regionTags.append(splitTag)         # Add it to the regionTags list
                        auditLogAddTags("regionTags", splitTag)
                    elif splitTag in romLang:               # If the tag can be found in the Language list
                        languageTags.append(splitTag)       # Add it to the languageTags list
                        auditLogAddTags("languageTags", splitTag)
                    else:                                   # Else if the tag cannot be matched
                        print("DEBUG: splittag in else is:", splitTag, type(splitTag))
                        if re.findall(r'PAL.*', splitTag):
                            regionTags.append("PAL")
                            auditLogAddTags("regionTags", splitTag)
                        else:
                            miscTags.append(splitTag)           # Add it to the miscTags list
                            auditLogAddTags("miscTags", splitTag)
        tags = { "regionTags" : regionTags, "languageTags" : languageTags, "miscTags" : miscTags } # Save scarped tag info to dictionary
        return tags

    def sortRom(rom, tags):                
        # Match by region  
        if tags["regionTags"]:                                          # If regionTags dictionary entry is not empty
            for tag in tags["regionTags"]:
                if "USA" in tags["regionTags"]:                             # Attempt to bail out early by matching on master sort region
                    moveRomAdd("USA", rom)
                    return 0
                elif tag == "Japan":
                    if len(tags["regionTags"]) == 1:
                        moveRomAdd("Japan", rom)
                        return 0
                    elif tags["regionTags"][1] in romRegion.keys(): 
                        if len(tags["languageTags"]) >= 1 and tags["languageTags"][0] != "Ja":
                            continue
                        else:
                            moveRomAdd("Japan", rom)
                            return 0
                    else:
                        moveRomAdd("Japan", rom)
                        return 0
                elif tag == "Europe":
                    moveRomAdd("Europe", rom)
                    return 0
                elif tag == "World":
                    if len(tags["regionTags"]) == 1:
                        if not tags["languageTags"] or "En" in tags["languageTags"]:
                            moveRomAdd("USA", rom)
                            return 0
                        else:
                            moveRomAdd("World", rom)
                            return 0
                    else:
                        if "PAL" in tags["regionTags"]:
                            moveRomAdd("Europe", rom)
                            return 0
                        else:
                            moveRomAdd("USA", rom)
                # We werent able to bail out
                if tag in romRegion["USA"]:
                    if not tags["languageTags"] or "En" in tags["languageTags"]:
                        moveRomAdd("USA", rom)
                        return 0
                    else:
                        moveRomAdd("World", rom)
                        return 0
                elif tag in romRegion["Japan"]:
                        moveRomAdd("Japan", rom)
                        return 0
                elif tag in romRegion["Europe"]:
                    moveRomAdd("Europe", rom)
                    return 0
                elif tag in romRegion["World"]:
                    moveRomAdd("World", rom)
                    return 0
                elif tag in romRegion["EurWor"]:
                    if "En" in tags["languageTags"]:
                        moveRomAdd("Europe", rom)
                        return 0
                    else:
                        moveRomAdd("World", rom)
                        return 0
                else:
                    continue
        elif tags["languageTags"]:
            if "En" in tags["languageTags"]:
                auditLogAddLn("USA", rom)
                ("DEBUG: *** REGIONLESS En ROM LEFT IN ROOT ***")
                return 0
            elif "Ja" in tags["languageTags"]:
                moveRomAdd("Japan", rom)
                print("DEBUG: *** REGIONLESS Jp ROM MOVED TO Japan ***")
                return 0
            else:
                moveRomAdd("World", rom)
                print("DEBUG: *** REGIONLESS ROM WITH Lng MOVED TO", worPath, " ***")
                return 0
        else:
            ("DEBUG: *** UNMATCHED ROM LEFT IN ROOT ***")
            return 1

    for rom in os.listdir(extPath):                                         # For each of the Rom Files in the extraction path
        print("DEBUG: WORKING ON ROM", rom, type(rom))
        if rom.endswith(".zip") and '[BIOS]' not in rom:                    # If the file is a archive, and is not a bios
            tags = gatherTags(rom)                                          # Scrape rom name for tags to process
            print("DEBUG: tags are:", tags, type(tags))
            results = sortRom(rom, tags)                                    # Process tags and move roms into folders
            print("DEBUG: results of romMove is", results, type(results))
            if results != 0:
                #auditLogAddLn("UnKwn", rom)
                print("DEBUG: *** Left in root folder ***")
        else:
            continue

# Maintains a log of actions performed by the script
def moveRom():
    global moveRomAdd       # Global sub-function to add lines to log buffer
    global romMover         # Does this need to be a global?
    global processBuffer
    global moveBuffer
    
    # Moves Processed Roms
    def romMover(srtFolder, rom):
        sortRomDest = extPath + "/" + srtFolder + "/" # FIX IN FUTURE THIS WILL CAUSE PROBLEMS WITH KEEPING US IN ROOT
        if not os.path.isdir(sortRomDest):
            makeDir(srtFolder)
        os.replace(extPath + "/" + rom, sortRomDest + rom)
        print("DEBUG: *** Moved", '\033[1m' + '\033[36m' + rom + '\033[0m', "to", '\033[1m' + '\033[91m' + srtFolder + '\033[0m', "***")
        return 0
    
    def processBuffer():
        for moveRomGrp in moveBuffer.keys():
            if moveBuffer[moveRomGrp]:
                print("DEBUG: moveRomGrp is:", moveRomGrp, type(moveRomGrp))
                if "ColTag" == moveRomGrp  or "Unkwn" == moveRomGrp:
                    # If either of these only call audit log write cause we're not moving
                    continue
                else:
                    for moveRomRom in moveBuffer[moveRomGrp]:
                        if romMover(moveRomGrp, moveRomRom) == 0:
                            continue
                        else:
                            print("ERROR: *** Failed to Move rom to", moveRomGrp, " ***")
                            exit(1)
            else:
                continue
    
    # Adds a line to the logline buffer sort catagory
    def moveRomAdd(srtGrp, rom):
        moveBuffer[srtGrp].append(rom)

    moveBuffer = { "ColTag": { "regionTags" : [], "languageTags" : [], "miscTags" : [] }, 
                   "USA": [], "Japan": [], "Europe": [], "World": [], "UnKwn": [] }
    
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
    moveRom()
    processRom()            # Processes roms based on region and language and moves them into sub-folders
    processBuffer()
    auditLogWrite()         # Writes log buffer to file
    exit(0)
	
# Calls the main routine on script startup
mainRoutine()               # Script entry point; execution begins here
