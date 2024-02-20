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
#####       0.10 Framework rewritten to be more object oriented

import re
import os
import subprocess
#import sys
from itertools import chain 
import argparse
from datetime import datetime

global now
global exeTime

now = datetime.now()
exeTime = now.strftime("%m/%d/%Y %H:%M:%S")

# Gets the arguments passed to the script at invocation
def argParser():
    global flags
    
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
    
    # Checks to see if the zip exists
    try:
        flags.zipFile
    # If the script was run without a zip file arguement
    except Exception:
        print("Error: Must specify a file")
        print("       Run the script again supplying a valid path to a No-Intro rom archive")
        print("         Ex: $ neni /home/user/Downloads/archive.zip")
        quit(1)
    else:                                           # If the script was run with arguments
        return flags

def checkZip(flags):    
    try:        # Check to see if the file exists
        os.path.isfile(flags.zipFile)
    except Exception:       # Error if the file cannot be found
        print("Error: Target File Cannot Be Found")
        print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
        print("         Ex: $ neni /home/user/Downloads/archive.zip")
        quit(1)
    else:   # If the zip file exists and is a file
        return flags.zipFile
            
def unzip(extPath, unzipCMD, zipFile):
    bashCMD = unzipCMD, '-d', '\'' + extPath + '\'', '\'' + zipFile + '\''
    if not bashCMD == "echo":
        pt.ds("Checking Extraction Directory " + extPath)
        if not os.path.isdir(extPath):
            pt.st("Decompressing archive")
            bash = execBash(' '.join(bashCMD))
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
    return 0

# Maintains a log of actions performed by the script
def moveRom(roms):
    # Creates the sort directories as needed
    def makeDir(srtFolder):
        if os.path.isdir(roms.extPath):
            if not os.path.isdir(roms.extPath + "/" + srtFolder):
                pt.ds("Making folder ", srtFolder, " at extraction path")
                os.mkdir(roms.extPath + "/" + srtFolder)
            else:
                pass
        else:
            pt.er("Unable to create sort directory, exiting...")
            exit(1)
                
    # Moves Roms to sort folders
    def romMover(extPath, srtFolder, rom):            
        sortRomDest = extPath + "/" + srtFolder + "/" # FIX IN FUTURE THIS WILL CAUSE PROBLEMS WITH KEEPING US IN ROOT
        if not os.path.isdir(sortRomDest):
            makeDir(srtFolder)
        os.replace(extPath + "/" + rom, sortRomDest + rom)
        pt.mv(rom, srtFolder)
        #print("DEBUG: *** Moved", '\033[1m' + '\033[36m' + rom + '\033[0m', "to", '\033[1m' + '\033[91m' + srtFolder + '\033[0m', "***")
        return 0
                 
    # Executes the sort list, moving the roms to their sort folders
    pt.dv("roms.romList")
    for moveRomGrp in roms.romList.keys():                                  # for each group in the sorted roms list
        if moveRomGrp != "unSrted" and moveRomGrp != "Unkwn":               # if the region is not the unsorted or unknown list
            if roms.romList[moveRomGrp]:                                    # If the sort region has entries
                for moveRomRom in roms.romList[moveRomGrp]:                 # For each rom in the rom list
                    if romMover(roms.extPath, moveRomGrp, moveRomRom) == 0: # Move the rom and check for success 
                        continue                                            # If successful move to next rom in list
                    else:                                                   # Fail if not successful
                        print("ERROR: *** Failed to Move rom to", moveRomGrp, " ***")
                        exit(1)
        else:                       # If the region group is unsorted or unknown
            continue                # Move to next region group

# Stores information about the rom collection, and performs operations on it
class romArchive():
    # Variables that are shares with all objects in class    
    romRegion = {
            "USA": ( "USA", "Canada" ),
            "Japan": ( "Japan", "null" ),
            "Europe": ( "Europe", "Australia", "PAL", "United Kingdom", "New Zealand" ),
            "EurWor": ( "Germany", "France", "Spain", "Italy", "Netherlands", "Sweden", "Scandinavia", "Denmark" ),
            "World": ( "World", "Asia", "China", "Brazil", "Taiwan", "Korea", "Russia", "Hong Kong", "Argentina", "Latin America", "Mexico" )
    }
    romLang = ( "En", "Fr", "De", "Es", "It", "Nl", "Ja", "Sv", "Pt", "No","Da", "Zh", "Fi", "PT-BR", "Pl", "Ru", "Ko", "Ar", "Ca", "Zh-Hans", 
                "Zh-Hant", "En-US", "Pt-PT", "En-GB", "Hu", "El", "Es-MX", "Es-XL", "Kw", "Ro", "Es-ES", "Yi", "Gd", "Cs", "Sl")
    romRegions = list(chain(*romRegion.values()))       # Get a list of all regions in the romRegion dictionary
    
    # Variables that are specific to the instanced object
    def __init__(roms, zipFile ):
        roms.zipfile = zipFile      # Stores the full path to the target archive
        roms.zipPath = ""           # Stores the directory in which the target archive is located
        roms.zipFn = ""             # Stores the full name of the target archive
        roms.zipFnRoot = ""         # Stores the name of the target archive without extension
        roms.zipFnExt = ""          # Stores the extension of the target archive
        roms.extPath = ""           # Stores the extraction target directory
        roms.romList = {            # Stores a list of all decompressed files in the extraction directory
                "unSrted": [], "USA": [], "Japan": [], "Europe": [], "World": [], "UnKwn": [] }
        roms.colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] }
        roms.totals = {"USA": 0, "Japan": 0, "Europe": 0, "World": 0, "UnKwn": 0, "Total": 0, "Tags": { } }
        
    def inspect(roms):
        roms.zipPath, roms.zipFn = os.path.split(roms.zipfile)                 # Get the path and full name from the zip passed to script
        roms.romsZipFnRoot, roms.zipFnExt = os.path.splitext(roms.zipFn)           # Get the base file name and extension from file name   
        roms.extPath = os.path.join(roms.zipPath, roms.romsZipFnRoot)              # Gets the target directory for file extraction from zip name
        #pt.dv(locals(), "roms.extPath", "roms.zipPath", "roms.zipFn", "roms.romsZipFnRoot", "roms.zipFnExt" )    # Prints a debug message with found variables
        if ".zip" not in roms.zipFnExt:  # If the extension is not .zip
            print("Error: Target File is no a Zip Archive")
            print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
            print("         Ex: $ neni /home/user/Downloads/archive.zip")
            quit(1)
        else:
            pt.de("zipFnExt is .zip else")
            return
    
    # Iterates through all of the files in the extraction directory and attempts to match them to a region
    def processRoms(roms):
        roms.getFiles()                                                 # Gathers and saves a list of all files in extraction target directory
        for romFile in roms.romList["unSrted"]:                         # For each of the Rom Files in the rom list class variable
            if romFile.endswith(".zip") and '[BIOS]' not in romFile:    # If the file is a archive, and is not a bios
                pt.dv(locals(), "romFile")                                        # Prints debug message with name of rom
                romTags = roms.scrape(romFile)                          # Calls method to scrape rom name for tags to process
                roms.collectTags(romTags)
                #pt.dv(locals(), "romTags", "roms.colTags")
                srtRegion = str(roms.sort(romFile, romTags))            # Calls method to determine the sort location of the rom
                if srtRegion == 1:
                    pt.wn("Unable to match", rom)                       # Prints debug message with name of skipped file
                    pt.mv(rom, 1)                                       # Prints debug substatement with location of skipped file
                else:
                    roms.romList[srtRegion].append(romFile)
                continue
            else:
                continue
        # get totals of roms and tags after processing
        roms.totals = roms.cntRoms(roms.romList)                         # Count the total processed roms
        pt.dv(locals(), "romFile")
        roms.totals["Tags"] = roms.cntTags(roms.colTags)                # Count the collected tags
        pt.ds("rom totals is: ", str(roms.totals))
        return 0
    
    # Gets a list of all roms in the extraction path to iterate through
    def getFiles(roms):
        roms.romList["unSrted"] = os.listdir(roms.extPath)

    def collectTags(roms, romTags):
        for tagGrp in roms.colTags:
            for tag in romTags[tagGrp]:
                roms.colTags[tagGrp].append(tag)
        
    # Takes the full file name of the current working file, scrapes it for tags and returns those tags
    def scrape(roms, romFile): # Scrapes tags from rom file name
        romTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] }
        
        pt.ds("Gathering tags...")
        romTags["unSrted"] = re.findall(r'\((?=[^(]*\))(.*?)\)', romFile)    # Scrape file name for all occurrences of (***) matching only complete (***)
        for tag in romTags["unSrted"]:                                       # For each of the collected tags
            tagSplit = tag.split(',')                                  # Split the tags on commas
            for splitTag in tagSplit:                                  # For each of the individual tags
                splitTag = splitTag.strip()                            # Strip whitespace
                if "+" in splitTag:
                    splitTag = splitTag.split('+')
                    tagSplit.extend(splitTag)
                    continue
                else:
                    if splitTag in roms.romRegions:                     # If the tag can be found in the regions list
                        romTags["regionTags"].append(splitTag)          # Add it to the regionTags list
                    elif splitTag in roms.romLang:                      # If the tag can be found in the Language list
                        romTags["languageTags"].append(splitTag)        # Add it to the languageTags list
                    else:                                               # Else if the tag cannot be matched
                        if re.findall(r'PAL.*', splitTag):              # >>>> NEED TO DO THIS BETTER REGEX
                            romTags["regionTags"].append("PAL")
                        else:
                            romTags["miscTags"].append(splitTag)        # Add it to the miscTags list
        return romTags
    
    # Takes a given romFile and its scraped tags and sorts it into one of the sort regions
    # Returns either the sort region or 1 for unmatched.
    def sort(roms, romFile, romTags):
        # Attempt to match by region  
        if romTags["regionTags"]:                                            # If regionTags dictionary entry is not empty
            for tag in romTags["regionTags"]:
                if "USA" in romTags["regionTags"]:                             # Attempt to bail out early by matching on master sort region
                    return "USA"
                elif tag == "Japan":
                    if len(romTags["regionTags"]) == 1:
                        return "Japan"
                    elif romTags["regionTags"][1] in romRegion.keys(): 
                        if len(romTags["languageTags"]) >= 1 and romTags["languageTags"][0] != "Ja":
                            continue
                        else:
                            return "Japan"
                    else:
                        return "Japan"
                elif tag == "Europe":
                    return "Europe"
                elif tag == "World":
                    if len(romTags["regionTags"]) == 1:
                        if not romTags["languageTags"] or "En" in romTags["languageTags"]:
                            return "USA"
                        else:
                            return "World"
                    else:
                        if "PAL" in romTags["regionTags"]:
                            return "Europe"
                        else:
                            return "USA"
                # We werent able to bail out
                if tag in romRegion["USA"]:
                    if not romTags["languageTags"] or "En" in romTags["languageTags"]:
                        return "USA"
                    else:
                        return "World"
                elif tag in romRegion["Japan"]:
                        return "Japan"
                elif tag in romRegion["Europe"]:
                    return "Europe"
                elif tag in romRegion["World"]:
                    return "World"
                elif tag in romRegion["EurWor"]:
                    if "En" in regionTags["languageTags"]:
                        return "Europe"
                    else:
                        return "World"
                else:
                    continue
        # If no region tags, but has language tags
        elif romTags["languageTags"]:
            if "En" in romTags["languageTags"]:
                print("DEBUG: *** REGIONLESS En ROM LEFT IN ROOT ***")
                return "USA"
            elif "Ja" in romTags["languageTags"]:
                print("DEBUG: *** REGIONLESS Jp ROM MOVED TO Japan ***")                
                return "Japan"
            else:
                print("DEBUG: *** REGIONLESS ROM WITH Lng MOVED TO", worPath, " ***")
                return "World"
        else:
            return 1
        return 1
        
    # Counts all the roms in the rom list
    def cntRoms(roms, romList):
        auditRomsCnted = []                                         # Create a temporary list to hold the rom counts
        # Get a count of roms on each of the sort lists
        for cntRomGrp in romList.keys():                       # For each of the sort groups in the rom list
            if cntRomGrp != "unSrted":                              # Don't count the unsorted rom list
                auditRomsCnted.append(cntRomGrp)                    # Add the sort group label to the list
                auditRomsCnted.append(len(roms.romList[cntRomGrp]))  # count the items and add it after the label
        # Create a dictionary to save the counts
        auditRomsTotals = { grp:ttl for (grp,ttl) in zip(auditRomsCnted[::2], auditRomsCnted[1::2])} # the first and every other as keys, second and every other as values   
        auditRomsTotals["Total"] = sum(auditRomsCnted[1::2])        # Save the total number of roms
        pt.dv(locals(), "auditRomsTotals")
        return auditRomsTotals
    
    # Takes a dictionary of collected tags and returns a dictionary with sorted tags, totals 
    # input format: colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] } 
    def cntTags(roms, colTags):
        pt.dv(locals(), "colTags")
        # Format: { Total: AllTags, "regionTags": { "group": AllGroup, tagTotals: [ [sorted list of tags] [totals] ]
        cntedTags = { "Total": 0, "regionTags": { "regionTags": 0, "tagTotals": [ [], [] ] },
                                  "languageTags": { "languageTags": 0, "tagTotals": [ [], [] ] },
                                  "miscTags": { "miscTags": 0, "tagTotals": [ [], [] ] } }

        cntedTags["Total"] = len(colTags["unSrted"])                            # Get the total number of tags scraped
        # Iterate through the collected tags and total them
        for tagGrp in list(colTags.keys())[1:]:                                 # For each of the categories, skipping the first
            if colTags[tagGrp]:                                                 # If the category has tags
                # Deduplicate and sort the tag collection
                tagsSorted = list(set(colTags[tagGrp]))                         # Dedpuelicate by using set, return a list
                tagsSorted.sort()                                               # Sort the Dedupelicated list 
                cntedTags[tagGrp][tagGrp] = len(colTags[tagGrp])                # Saves totals for tag group to group sub dictionary value
                for tag in tagsSorted:                                          # For each of the tags in the sorted list
                    # Count occurrences of tag in collection and append to list
                    tagCnt = tagsSorted.count(tag)
                    # Append tag to cntedTags tag list
                    cntedTags[tagGrp]["tagTotals"][0].append(str(tag))
                    cntedTags[tagGrp]["tagTotals"][1].append(int(tagCnt))
            else: 
                continue
        pt.dv(locals(), "cntedTags")
        return cntedTags

def auditLog(flags, extPath, romList, romTotals):
    # Determine what the audit log file will be named
    if flags.relVers:
        pt.ds("join(flags.relVers) is: " + ' '.join(flags.relVers))
        auditFn = "[ " + ' '.join(flags.relVers) + " No-Intro Set ]"
    #else:
        #auditFn = "[ " + zipFn + " No-Intro Set ]"  # THIS NEEDS TO BE FIXED zipFN undefined
        
    # Processes audit log buffers and writes them to a file in the extraction directory
    auditFPath = extPath + "/" + auditFn
    auditFile = open(auditFPath, "a")               # CHECK AND DELETE IF THERE
            
    # Write the audit log header information
    auditFile.write("No Effort No Intro" + '\n')
    auditFile.write("   Audit Log" + '\n\n')
    auditFile.write("Created on:    " + exeTime + '\n')
    auditFile.write("Processed:     " + flags.zipFile + '\n')
    auditFile.write("Extracted to:  " + extPath + '\n')
    auditFile.write("Total Files:   " + str(romTotals["Total"]) + '\n\n')
    
    # Process the log buffer and write it to the audit file
    # Writes the collected tags and totals to file:
    # romTotals > Tags > regionTags > tagTotals  
    #rom totals is:  'Tags': {'Total': 6, 
    #'regionTags': {'regionTags': 2, 'tagTotals': [['Japan', 'USA'], [1, 1]]}, 'languageTags': {'languageTags': 5, 'tagTotals': [['De', 'En', 'Fr', 'Ja'], [1, 1, 1, 1]]}, 'miscTags': {'miscTags': 3, 'tagTotals': [['Beta', 'proto', 'test'], [1, 1, 1]]}}}
    
    auditFile.write("### " + str(romTotals["Tags"]["Total"]) + " Tags Were Scraped From File Names  ###" + '\n')
    for tagGrp in list(romTotals["Tags"])[1:]:
        if tagGrp == "regionTags":
            auditFile.write(str(romTotals["Tags"][tagGrp][tagGrp]).rjust(6, ' ') + " Region Tags" + '\n')
        elif tagGrp == "languageTags":
            auditFile.write(str(romTotals["Tags"][tagGrp][tagGrp]).rjust(6, ' ') + " Language Tags" + '\n')
        elif tagGrp == "miscTags":
            auditFile.write(str(romTotals["Tags"][tagGrp][tagGrp]).rjust(6, ' ') + " Miscellaneous Tags" + '\n')
        for logLn in romTotals["Tags"][tagGrp]["tagTotals"][1]:
            lnIndex = int(romTotals["Tags"][tagGrp]["tagTotals"][1].index(logLn))
            auditFile.write(str(romTotals["Tags"][tagGrp]["tagTotals"][1][lnIndex]).rjust(6, ' ') + 
                " " + str(romTotals["Tags"][tagGrp]["tagTotals"][0][lnIndex]) + '\n')
        # Add blank line at end of list for formatting  
        auditFile.write('\n')
        continue
    
    # Writes the results of the rom sort
    for srtGrp in list(romList)[1:]:
        if romList[srtGrp]:
            if srtGrp == "UnKwn":
                auditFile.write("###  " + str(romTotals[srtGrp]) + " Files Were Unmatched  ###" + '\n')
            else:
                auditFile.write("###  " + str(romTotals[srtGrp]) + " Files Matched the " + str(srtGrp) + " Region  ###" + '\n')

            for logLn in romList[srtGrp]:
                auditFile.write(str(logLn) + '\n')
        else:
            auditFile.write('\n')
            continue
        auditFile.write('\n')
    auditFile.close()
            
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
        if mvLoc != 1:
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

# BASH ENGINE: Runs commands in a bash shell
def execBash(execBash_CMD):    
    print("DEBUG: execbash bashCMD is", execBash_CMD)
    bash=subprocess.run(execBash_CMD, shell = True, executable = "/bin/bash", capture_output=True)
    print("DEBUG: execbash bash is", bash, type(bash))
    return bash

# Defines the order subroutines are executed
def mainRoutine():
    flags = argParser()                                              # Gets arguments
    roms = romArchive( checkZip(flags) )                             # Performs sanity checks on target file, initializes roms class
    roms.inspect()                                                   # Gathers information about the target zip file
    unzip(roms.extPath, flags.unzipCMD, roms.zipfile)                # Unzips target file
    roms.processRoms()                                               # Processes roms based on region and language and moves them into sub-folders
    moveRom(roms)                                                    # Moves rom files to sort folders
    auditLog(flags, roms.extPath, roms.romList, roms.totals)         # Writes log buffer to file
    exit(0)
	
# Calls the main routine on script startup
mainRoutine()               # Script entry point; execution begins here
