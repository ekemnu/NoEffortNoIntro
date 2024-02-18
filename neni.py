#####   No Effort No-Intro
#####	John Loreth
#####	2024
#####	v0.10
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
#####       0.8  Further design changes and refinements to audit log
#####       0.9  Added a message buffer
#####       0.10 Reworked to be more object oriented

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



class pt:
    class color:
       p = '\033[95m'      # Purple
       c = '\033[96m'        # Cyan
       dc = '\033[36m'    # Dark Cyan
       b = '\033[94m'        # Blue
       g = '\033[92m'       # Green
       y = '\033[93m'      # Yellow
       r = '\033[91m'         # Red
       b = '\033[1m'         # Bold
       u = '\033[4m'    # Underline
       o = '\033[0m'          # off
        
    class c:
        # Debug Colors
        g = '\033[0m' + '\033[92m'                  # Off and Green 
        gb = '\033[0m' + '\033[92m' + '\033[1m'     # Off and Green and bold
        gu = '\033[0m' + '\033[92m' + '\033[4m'     # Off and Green and underline
        # Moved Colors
        c = '\033[0m' + '\033[36m'                  # Off and Dark Cyan
        cb = '\033[0m' + '\033[36m' + '\033[1m'     # Off and Dark Cyan and Bold
        cu = '\033[0m' + '\033[36m' + '\033[4m'     # Off and Dark Cyan and Underline
        yb = '\033[0m' + '\033[93m' + '\033[1m'     # Off and Yellow and Bold
        # Error Colors
        r = '\033[0m' + '\033[91m'                  # Off and red 
        rb = '\033[0m' + '\033[91m' + '\033[1m'     # Off and red and bold
        ru = '\033[0m' + '\033[91m' + '\033[4m'     # Off and red and underline
        # Style
        b = '\033[1m'    # Bold
        u = '\033[4m'    # Underline
        o = '\033[0m'    # off
        
    # Prints status messages
    # def st( message, subStat? ) > " NeNi:     make move buffer a class? can do line; pt.dv(blah)
    def st(stMsg, sub):
        if not sub:
            print("NeNI:", stMsg)
        else:
            print("NeNI:     ", stMsg)
    
    # Prints non-fatal warning messages
    # pt.wn( message )
    def wn(*wnMsg):
        wnMsg = ' '.join(wnMsg)
        print("NeNI:", pt.c.yb + "WARNING:", pt.c.o + str(wnMsg) )

    # Prints Error Messages and gives advice to resolve
    # pt.er([ erMsg, anything, erAdv ]) > " NeNI: ERROR: errorMessage " and " NeNI:   >>> resolveAdvice "
    def er(erMsg, erInfo):
        print("NeNI:", pt.c.rb + "ERROR:", pt.c.o + erMsg )
        if erInfo and erInfo != "s":
            print("NeNI:", pt.c.rb + "ERROR:", pt.c.o + str(erMsg) + " " + str(erInfo) )
        else:
            print("NeNI:   >>>", str(erAdv) )
    # Prints messages to notify user of file moves
    # pt.mv(romName, moveLocation) > " NeNi: Moved: romName to moveLocation "
    def ma(dmRom, dmLoc):
            print("NeNI: Rom", pt.c.gb + dmRom, pt.c.o + "Matched", pt.c.yb + dmLoc + pt.c.o)
            
    # Prints messages to notify user of file moves
    # pt.mv(romName, moveLocation) > " NeNi: Moved: romName to moveLocation "
    def mv(mvRom, mvLoc):
        if mvLoc is not 1:
            print("NeNI: Moved", pt.c.cb + mvRom, pt.c.o + "to:", pt.c.yb + mvLoc + pt.c.o)
        else:
            print("NeNI: Left", pt.c.cb + mvRom, pt.c.o + "in", pt.c.yb + "Root Directory" + pt.c.o)
    
    # Takes general debug messages and prints the result
    # pt.ds(string)
    def ds(*dsMsg):
        print("NeNI:", pt.c.b + "DEBUG:", pt.c.gb + ' '.join((dsMsg[:])) + pt.c.o)
        
    # Prints working on rom mesages
    # pt.dr
    def dp(dpRom, *dpSkip):
        if not dpSkip:
            print("NeNI:", pt.c.b + "DEBUG:", pt.c.gb + "Processing " + pt.c.o + "file", pt.c.gb + dpRom, pt.c.o + "...")
        else:
            print("NeNI:", pt.c.b + "DEBUG:", pt.c.gb + "Processing " + pt.c.o + "file", pt.c.gb + dpRom, pt.c.o + "...")
    
    # dvVar = [ [variable] , [variable name]]
    # pt.dv( [ "var1", "var2 in", "var3", "var4", ... ], [ var1, var2, var3, var4, ... ] ]
    # pt.dv( { "var1": var1, "var2 in": var2, "var3 blah": var3, "var4": var4, ... } )
    # pt.dv( {"var1":var1})
            
    # Takes a list of variables and prints them with their values and types
    def dv(dvGlob, *dvVar):
        for var in dvVar:
            print("NeNI:", pt.c.b + "DEBUG:", pt.c.gb + var, pt.c.o + "is:", pt.c.gb + str(dvGlob[var]) + pt.c.o + " " + str(type(dvGlob[var])))
    
    # Prints a debug message with a string for a location to mark entering sections of code
    # pt.de(location) > " NeNI: DEBUG: Entered location "
    def de(deLoc):
        print("NeNI:", pt.c.b + "DEBUG:", pt.c.b + "Entered", pt.c.gb + deLoc + pt.c.o)
              
              
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
        
        def cntRoms(cntRomsBuffer):
            auditRomsCnted = []
            for cntRomGrp in cntRomsBuffer.keys():
                if cntRomGrp != "ColTag":
                    auditRomsCnted.append(cntRomGrp)
                    auditRomsCnted.append(len(cntRomsBuffer[cntRomGrp]))
            auditRomsTotals = { grp:ttl for (grp,ttl) in zip(auditRomsCnted[::2], auditRomsCnted[1::2])}  
            auditRomsTotals["Total"] = sum(auditRomsCnted[1::2])
            return auditRomsTotals

        def cntTags(tagCollection):
            for auditLogTagGrp in tagCollection.keys():                                            # For each of the catagories in the Collected Tags
                if tagCollection[auditLogTagGrp]:                                           # If the catagory has tags
                    tagCollection[auditLogTagGrp] = [ tagCollection[auditLogTagGrp], [], [] ]
                    # Deduplicate and sort the tag collection
                    tagCollection[auditLogTagGrp][1] = list(set(moveBuffer["ColTag"][auditLogTagGrp][0]))      # Dedpuelicate by using set, return a list
                    tagCollection[auditLogTagGrp][1].sort()                                                 # Sort the Dedupelicated list
                    tagCollection[auditLogTagGrp][2].insert(0, len(tagCollection[auditLogTagGrp][1]))       # Add blank space as first item for formatting
                    tagCollection[auditLogTagGrp][1].insert(0, auditLogTagGrp.upper() + ":")             # Add the tag catagory in uppercase as first item
                    for auditLogTagTag in tagCollection[auditLogTagGrp][1][1:]:                                 # For each of the tags in the sorted list
                        # Count occurances of tag in tag collection and append to list
                        tagCollection[auditLogTagGrp][2].append(str(tagCollection[auditLogTagGrp][0].count(auditLogTagTag)))
                else: 
                    continue
                tagCollection[auditLogTagGrp][1].append("")                                      # Add blank space as first item for formatting
                tagCollection[auditLogTagGrp][2].append("")
            return tagCollection     # Return counted lists to add them to the moveBuffer
        
        moveBuffer["Totals"] = cntRoms(moveBuffer)
        moveBuffer["ColTag"] = cntTags(moveBuffer["ColTag"])
        
        # Write the audit log header information
        auditFile.write("No Effort No Intro" + '\n')
        auditFile.write("   Audit Log" + '\n\n')
        auditFile.write("Created on:    " + exeTime + '\n')
        auditFile.write("Processed:     " + flags.zipFile + '\n')
        auditFile.write("Extracted to:  " + extPath + '\n')
        auditFile.write("Total Files:   " + str(moveBuffer["Totals"]["Total"]) + '\n\n')
        
        # Process the log buffer and write it to the audit file
        for auditLogGrp in moveBuffer.keys():
            if auditLogGrp == "ColTag":
                auditFile.write("###  Tags That Were Scraped From File Names  ###" + '\n')
                for auditLogTagGrp in moveBuffer[auditLogGrp]:
                    print("tag group is", moveBuffer[auditLogGrp])
                    for auditLogLn in moveBuffer[auditLogGrp][auditLogTagGrp][1]:
                        index = int(moveBuffer[auditLogGrp][auditLogTagGrp][1].index(auditLogLn))
                        auditFile.write(str(moveBuffer[auditLogGrp][auditLogTagGrp][2][index]).rjust(6, ' ') + " " + str(moveBuffer[auditLogGrp][auditLogTagGrp][1][index]) + '\n')
                # Add blank line at end of list for formatting  
                auditFile.write('\n')
                continue
            elif auditLogGrp == "UnKwn":
                auditFile.write("###  Files That Were Unmatched  ###" + '\n')
            else:
                if auditLogGrp != "Totals":
                    auditFile.write("###  " + str(moveBuffer["Totals"][auditLogGrp]) + " Files Matched the " + auditLogGrp + " Region  ###" + '\n')
                    for auditLogLn in moveBuffer[auditLogGrp]:
                        auditFile.write(str(auditLogLn) + '\n')
                    else:
                        auditFile.write('\n')
                        continue
            auditFile.write('\n')
        auditFile.close()
    
    # Determine what the audit log file will be named
    if flags.relVers:
        pt.ds("join(flags.relVers) is: " + ' '.join(flags.relVers))
        auditFn = "[ " + ' '.join(flags.relVers) + " No-Intro Set ]"
    else:
        auditFn = "[ " + zipFn + " No-Intro Set ]"

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
        #print("DEBUG: Globals before is", globals(), type(globals()))
        #print("DEBUG: Locals before is", locals(), type(locals()))
        pt.dv(globals(), "zipPath", "zipFn", "zipFnRoot", "zipFnExt" )
        #print("DEBUG: zipPath is:", zipPath, type(zipPath), "zipFn is:", zipFn, type(zipFn), "zipFnRoot is:", zipFnRoot, type(zipFnRoot), "zipFnExt is:", zipFnExt, type(zipFnExt))
        if ".zip" not in zipFnExt:
            print("Error: Target File is no a Zip Archive")
            print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
            print("         Ex: $", scriptFn, "/home/user/Downloads/archive.zip")
            quit(1)
        else:
            pt.de("zipFnExt is .zip else")
            pass
    		
def unzip():
        global extPath

        extPath = os.path.join(zipPath, zipFnRoot)
        bashCMD = flags.unzipCMD, '-d', '\'' + extPath + '\'', '\'' + zipFile + '\''
        if not bashCMD == "echo":
            pt.ds("Checking Extraction Directory " + extPath)
            if not os.path.isdir(extPath):
                pt.st("Decompressing archive")
                execBash(' '.join(bashCMD))
                if bash.returncode == 0:
                    pt.st("Sucessfully decompressed archive to: " + extPath, sub)
                else:
                    pt.er("Archive Decompression Failed", bash.stderr)
                    quit(1)
            else:
                if flags.unzipCMD.startswith('u'):
                    pt.er("Error: Decompression Target Directory Already Exists, exiting...")
                    quit(1)
                else:
                    pt.ds("This is a Dry Run: Skipping Decompression")
                    pass
        else:
            pt.ds("passed unzip because of dry run")
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
                pt.ds("Making folder ", srtFolder, " at extraction path")
                os.mkdir(extPath + "/" + srtFolder)
            else:
                pass
        else:
            pt.er("Unable to create sort directory, exiting...")
            exit(1)

    def gatherTags(rom):    # Scraps tags from Rom file name
        regionTags = []     # Create empty list for region tags
        languageTags = []   # Create empty list for language tags
        miscTags = []       # Create empty list for misc tags
        
        pt.ds("Gathering tags...")
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
                        if re.findall(r'PAL.*', splitTag):
                            regionTags.append("PAL")
                            auditLogAddTags("regionTags", splitTag)
                        else:
                            miscTags.append(splitTag)           # Add it to the miscTags list
                            auditLogAddTags("miscTags", splitTag)
        tags = { "regionTags" : regionTags, "languageTags" : languageTags, "miscTags" : miscTags } # Save scarped tag info to dictionary
        pt.dv(locals(), "tags")
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
                print("DEBUG: *** REGIONLESS En ROM LEFT IN ROOT ***")
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
            return 1

    for rom in os.listdir(extPath):                                         # For each of the Rom Files in the extraction path
        if rom.endswith(".zip") and '[BIOS]' not in rom:                    # If the file is a archive, and is not a bios
            pt.dp(rom)                                                      # Prints debug message with name of rom
            tags = gatherTags(rom)                                          # Scrape rom name for tags to process
            results = sortRom(rom, tags)                                    # Process tags and move roms into folders
            if results != 0:
                pt.wn("Unable to match", rom)                               # Prints debug message with name of skipped file
                pt.mv(rom, 1)                                               # Prints debug substatement with location of skipped file
        else:
            continue

# Maintains a log of actions performed by the script
def moveRom():
    global moveRomAdd       # Global sub-function to add lines to log buffer
    global romMover         # Does this need to be a global?
    global processBuffer
    global moveBuffer
    
    # Adds a line to the logline buffer sort catagory
    def moveRomAdd(srtGrp, rom):
        moveBuffer[srtGrp].append(rom);     pt.ma(rom, srtGrp)
    
    def processBuffer():
        for moveRomGrp in moveBuffer.keys():
            if moveBuffer[moveRomGrp]:
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
                
    # Moves Processed Roms
    def romMover(srtFolder, rom):
        sortRomDest = extPath + "/" + srtFolder + "/" # FIX IN FUTURE THIS WILL CAUSE PROBLEMS WITH KEEPING US IN ROOT
        if not os.path.isdir(sortRomDest):
            makeDir(srtFolder)
        os.replace(extPath + "/" + rom, sortRomDest + rom)
        pt.mv(rom, srtFolder)
        #print("DEBUG: *** Moved", '\033[1m' + '\033[36m' + rom + '\033[0m', "to", '\033[1m' + '\033[91m' + srtFolder + '\033[0m', "***")
        return 0

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
