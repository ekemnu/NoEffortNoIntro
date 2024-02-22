#####   No Effort No-Intro
#####	John Loreth
#####	2024
#####   0.14
#####
#####   Process and extracts No-Intro Rom Archives, sorts by region into sub directories
#####
#####   Version history:
#####		0.1  Basic bash script
#####       0.2  Rewritten in Python
#####       0.3  Improved Tag Scraping Logic
#####       0.4  Functionalized rom movement
#####       0.5  Functionalized sort dir creation to create only as needed
#####       0.6  Added move buffer for --pretend mode
#####       0.7  Rewrote audit log to use move buffer data instead of independent buffer
#####       0.8  Further design changes and refinements to audit log
#####       0.9  Added a message buffer
#####       0.10 Framework rewritten to be more loosely coupled and object oriented, reworked audit file handling
#####       0.11 Reworked audit file creation, messenger improvements, removed debug functions, bug fixes
#####       0.12 Added ability to skip extraction, skip audit write, and set detestation and extraction directories
#####       0.13 Added ability to choose home sort region
#####       0.14 Handle multiple archives, create object instance for each rom from each archive

import argparse
import sys
import os
import shutil
import re
from itertools import chain 
from datetime import datetime

global exeTime

now = datetime.now()
exeTime = now.strftime("%m/%d/%Y %H:%M:%S")

# Gets the arguments passed to the script at invocation
def argParser():
    parser = argparse.ArgumentParser( description='Processes given No-Intro archive, sorts by region into sub directories',
                        epilog='Written by John Loreth 2024')
    parser.add_argument('zipFile')
    parser.add_argument('-a', '--audit', action=argparse.BooleanOptionalAction,
                        help='Skips writing audit file')
    parser.add_argument('-d', '--destination', action='store', nargs='?', dest='outDest',
                        help='Specifies an output directory for processed roms')
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction,
                        help='Prints debug messages to the console')
    parser.add_argument('-t', '--home-turf', action='store', nargs='?',
                        default='USA', dest='homeRgn', choices=['USA', 'Europe', 'World'],
                        help='Specifies the home sort region (default: USA)')
    parser.add_argument('-p', '--pretend', action=argparse.BooleanOptionalAction,
                        help='Runs the script without making any changes')
    parser.add_argument('-e', '--extract-to', action='store', nargs='?',
                        default='/tmp', dest='extTo',
                        help='Specifies a target temporary working directory for extraction (default: /tmp)')
    parser.add_argument('-r', '--release', action='store', dest='relVers',
                        help='Specify No-Intro release information to include after processing')
    parser.add_argument('-x', '--skip-extraction', action=argparse.BooleanOptionalAction,
                        help='Skips extraction of the target archive, looks for a directory with that name to process')
    parser.add_argument('-v', '--verbose', action=argparse.BooleanOptionalAction,
                        help='Prints additional information to the console')
    parser.add_argument('--version', action='version', version='NenI 0.14')
    
    flags = parser.parse_args()
    return flags

def checkZip(flags):    
    m.st("Checking target archive...")
    # Check to see if the file exists
    if not os.path.isfile(flags.zipFile):
        m.er("Target File Cannot Be Found")
        m.ei("Check that you've supplied a valid path to a No-Intro zip archive and run NeNi again")
        m.ei("  Ex: $ neni /home/user/Downloads/archive.zip")
        m.ex("Error")
        quit(1)
    else:   # If the zip file exists and is a file
        # Get the full path of the zip file
        zipFile = os.path.abspath(flags.zipFile)
        return zipFile

# Creates sort directories as needed and moves sorted files into directories
def moveRom_old(move, extPath, outDest, zipPath, romList, homeRgn, ptend):
    # Creates the sort directories as needed
    def makeDir(extPath, srtFolder):
        if os.path.isdir(extPath):
            if not os.path.isdir(extPath + "/" + srtFolder):
                m.sb("Making folder", srtFolder, "at extraction path")
                os.mkdir(extPath + "/" + srtFolder)
            else:
                pass
        
    # Executes the sort list, moving the roms to their sort folders
    m.dv(locals(), "romList")
    m.st("Moving Sorted Roms ...")
    if not ptend:
        for moveRomGrp in list(romList.keys())[1:5]:                         # for each group in the sorted roms list
            if romList[moveRomGrp]:                                         # If the sort region has entries
                if homeRgn == moveRomGrp:
                    srtRomDest = extPath + "/"
                else:
                    srtRomDest = extPath + "/" + moveRomGrp + "/"
                if not os.path.isdir(srtRomDest):
                    makeDir(extPath, moveRomGrp)
                for moveRomRom in romList[moveRomGrp]:                      # For each rom in the rom list
                    if move(extPath, srtRomDest, moveRomGrp, homeRgn, moveRomRom) == 0:      # Move the rom and check for success 
                        continue                                            # If successful move to next rom in list
                    else:                                                   # Fail if not successful
                        m.er("Failed to move rom to", moveRomGrp)
                        m.ex("Error")
                        sys.exit(1)
        # Move the working directory to the final destination
        m.st("Moving Working Directory to Output Destination...")
        if outDest != extPath:
            m.dv(locals(), "outDest", )
            shutil.move(extPath, outDest)
        else:
            m.sb("Working Extraction Directory and Destination are Identical, Skipping")
        return 0
    else:
        m.n("Skipping Rom Move Because We're Pretending")
        return 0

# Creates sort directories as needed and moves sorted files into directories
def moveRom(move, extPath, outDest, zipPath, romList, homeRgn, ptend):
    # Creates the sort directories as needed
    def makeDir(extPath, srtFolder):
        if os.path.isdir(extPath):
            if not os.path.isdir(extPath + "/" + srtFolder):
                m.sb("Making folder", srtFolder, "at extraction path")
                os.mkdir(extPath + "/" + srtFolder)
            else:
                pass
        
    # Executes the sort list, moving the roms to their sort folders
    m.dv(locals(), "romList")
    m.st("Moving Sorted Roms ...")
    if not ptend:
        # Iterate through the registry of romFile object instances
        for rom in rArch.romFiles:                         # for each group in the sorted roms list
            # Get the index of the instance on the list
            # Set rom to that instance
            rom = rArch.romFiles.index(rom) <<<<<
            # Set the move location based on user selectable home region
            if homeRgn == rom.srtRegion:
                # >>>>> should i just pass here?
                srtRomDest = extPath + "/"                              # Sort location is root extraction directory
            else:
                srtRomDest = extPath + "/" + moveRomGrp + "/"           # Sort location is a master region subfolder
                # If the sort directory doesn't exist, create it
                if not os.path.isdir(srtRomDest):
                    makeDir(extPath, moveRomGrp)
            # move the rom to it's destination
            if move(extPath, srtRomDest, moveRomGrp, homeRgn, moveRomRom) == 0: # Move the rom and check for success 
                continue                                                        # If successful move to next rom in list
            else:                                                               # Fail if not successful
                m.er("Failed to move rom to", moveRomGrp)
                m.ex("Error")
                sys.exit(1)
        # Move the working directory to the final destination
        m.st("Moving Working Directory to Output Destination...")
        if outDest != extPath:
            m.dv(locals(), "outDest", )
            shutil.move(extPath, outDest)
        else:
            m.sb("Working Extraction Directory and Destination are Identical, Skipping")
        return 0
    else:
        m.n("Skipping Rom Move Because We're Pretending")
        return 0
            
# Stores information about the rom collection, and performs operations on it
class rArch(object):
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
    def __init__(rArch, zipFile):
        rArch.zipFile = zipFile      # Stores the full path to the target archive
        rArch.zipPath = ""           # Stores the directory in which the target archive is located
        rArch.zipFn = ""             # Stores the full name of the target archive
        rArch.zipFnRoot = ""         # Stores the name of the target archive without extension
        rArch.zipFnExt = ""          # Stores the extension of the target archive
        rArch.extPath = ""           # Stores the extraction target directory
        rArch.outDest = ""           # Stores the final destination of the processed roms
        rArch.romList = {            # Stores a list of all decompressed files in the extraction directory
                "unSrted": [], "USA": [], "Japan": [], "Europe": [], "World": [], "UnKwn": [] }
        rArch.colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] }           # Stores scraped tags
        rArch.totals = {"USA": 0, "Japan": 0, "Europe": 0, "World": 0, "UnKwn": 0, "Total": 0, "Tags": { } } # Stores totals
        rArch.romFiles = []          # Create a list to store all instances of the romFile subclass
    
    
    # Iterates through all of the files in the extraction directory and attempts to match them to a region
    def processRoms(rArch, extTo, outDest, ptend, sXtract):
        # Gather information about target archive
        rArch.inspect(rArch.zipFile, extTo, outDest)
        #m.dv(locals(), "rArch.zipFile", "rArch.extPath", "rArch.zipPath", "rArch.zipFn", "rArch.zipFnRoot", "rArch.zipFnExt", "rArch.outDest" )
        # Decompress the target archive
        rArch.unzip(rArch.extPath, rArch.zipPath, rArch.zipFile, ptend, sXtract)    # Unzips target file
        # Get a list of all files decompressed into target directory    
        rArch.getFiles()                                                            # Gathers and saves a list of all files in extraction target directory
        m.st("Sorting Roms...")
        for rom in rArch.romList["unSrted"]:                                        # For each of the Rom Files in the rom list class variable
            if rom.endswith(".zip") and '[BIOS]' not in rom:                        # If the file is a archive, and is not a bios
                m.wk(rom)                                                           # Prints message with name of rom
                # Initialize a new instance of a romFile object
                romObj = romFile(rom, rArch.zipFn, rArch.zipPath)
                # Rename it to match the file name of the working rom
                romObj.__name = romObj.romFiles.index(rom)
                m.dv(locals(), "romObj")
                # Scrape tags from the working rom
                romObj.tags = romObj.scrape()                                   # Calls method to scrape rom name for tags to process
                print(romObj.tags)
                # Collects the tags into the archive
                rArch.collectTags(romObj.tags)
                #m.dv(locals(), "romTags", "rArch.colTags")
                # Attempts to sort the rom into one of the master sort regions
                romObj.srtRegion = str(romObj.sort(rom, romObj.tags))         # Calls method to determine the sort location of the rom
                if romObj.srtRegion == "UnKwn":
                    # Add rom to the unknown list
                    rArch.romList[romObj.srtRegion].append(rom)
                    m.wn("Unable to match", rom)                       # Prints debug message with name of skipped file
                    m.lf(rom)                                          # Prints debug substatement with location of skipped file
                else:
                    rArch.romList[romObj.srtRegion].append(rom)
                continue
            else:
                continue
        # get totals of roms and tags after processing
        rArch.totals = rArch.cntRoms(rArch.romList)                         # Count the total processed roms
        m.dv(locals(), "rom")
        rArch.totals["Tags"] = rArch.cntTags(rArch.colTags)                # Count the collected tags
        m.ds("rom totals is: ", str(rArch.totals))
        return romObj.move
    
    # Gathers information about the target archive
    def inspect(rArch, zipFile, extTo, outDest):
        rArch.zipPath, rArch.zipFn = os.path.split(zipFile)             # Get the path and full name from the zip passed to script
        rArch.zipFnRoot, rArch.zipFnExt = os.path.splitext(rArch.zipFn)  # Get the base file name and extension from file name   
        rArch.extPath = os.path.join(extTo, rArch.zipFnRoot)            # Gets the target directory for file extraction from zip name
        if not outDest:
            m.de("outdest set")
            rArch.outDest = rArch.zipPath                               # Sets the final destination to be the same as the target archive
        else:
            rArch.outDest = outDest                                    # Sets the final destination to location given by user
        # Check if the archive has a .zip extension 
        if ".zip" not in rArch.zipFnExt:                               # If the extension is not .zip
            print("Error: Target File is no a Zip Archive")
            print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
            print("         Ex: $ neni /home/user/Downloads/archive.zip")
            quit(1)
        else:
            m.de("zipFnExt is .zip else")
            return 0
    
    def unzip(rArch, extPath, zipPath, zipFile, ptend, sXtract):
        if not ptend and not sXtract:
            m.dv(locals(), "extPath", "zipPath", "zipFile", "ptend")
            m.st("Checking Extraction Directory...", extPath)
            if not os.path.isdir(extPath):
                m.st("Decompressing Archive...")
                try: 
                    shutil.unpack_archive(zipFile, extPath, "zip")
                except:
                    m.er("Archive Decompression Failed")
                    m.ex("Error")
                    sys.exit(1)
                else:
                    m.st("Successfully Decompressed", zipFile, "to:", extPath)
                    return(0)
            else:
                m.er("Decompression Target Directory Already Exists")
                m.ex("Error")
                sys.exit(1)
        else:
            m.n("Skipping Decompression Because We're Pretending")
            return 0
    
    # Gets a list of all roms in the extraction path to iterate through
    def getFiles(rArch):
        try:
            rArch.romList["unSrted"] = os.listdir(rArch.extPath)
        except:
            m.er("Unable to Process Extracted Files")
            m.ei("No Such File or Directory")
            m.ex("Error")
            sys.exit(1)
            
    def collectTags(rArch, romTags):
        for tagGrp in rArch.colTags:
            for tag in romTags[tagGrp]:
                rArch.colTags[tagGrp].append(tag)
     
    # Counts all the roms in the rom list
    def cntRoms(rArch, romList):
        auditRomsCnted = []                                         # Create a temporary list to hold the rom counts
        # Get a count of roms on each of the sort lists
        for cntRomGrp in romList.keys():                       # For each of the sort groups in the rom list
            if cntRomGrp != "unSrted":                              # Don't count the unsorted rom list
                auditRomsCnted.append(cntRomGrp)                    # Add the sort group label to the list
                auditRomsCnted.append(len(rArch.romList[cntRomGrp]))  # count the items and add it after the label
        # Create a dictionary to save the counts
        auditRomsTotals = { grp:ttl for (grp,ttl) in zip(auditRomsCnted[::2], auditRomsCnted[1::2])} # the first and every other as keys, second and every other as values   
        auditRomsTotals["Total"] = sum(auditRomsCnted[1::2])        # Save the total number of roms
        m.dv(locals(), "auditRomsTotals")
        return auditRomsTotals
    
    # Takes a dictionary of collected tags and returns a dictionary with sorted tags, totals 
    # input format: colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] } 
    def cntTags(rArch, colTags):
        #m.dv(locals(), "colTags")
        # Format: { Total: AllTags, "regionTags": { "group": AllGroup, tagTotals: [ [sorted list of tags] [totals] ]
        #cntedTags = { "Total": 0, "regionTags": { "regionTags": 0, "tagTotals": [ [], [] ] },
        #                          "languageTags": { "languageTags": 0, "tagTotals": [ [], [] ] },
        #                          "miscTags": { "miscTags": 0, "tagTotals": [ [], [] ] } }

        cntedTags = { "Total": 0, "regionTags": { "Total": 0 }, "languageTags": { "Total": 0 }, "miscTags": { "Total": 0 } }
        cntedTags["Total"] = len(colTags["unSrted"])                            # Get the total number of tags scraped
        
        #for i in range(len(keys)):
        #dynamic_dict[keys[i]] = values[i]
    
        # Iterate through the collected tags and total them
        for tagGrp in list(colTags.keys())[1:]:                                 # For each of the categories, skipping the first
            if colTags[tagGrp]:                                                 # If the category has tags
                # Deduplicate and sort the tag collection
                tagsSorted = list(set(colTags[tagGrp]))                         # Dedpuelicate by using set, return a list
                tagsSorted.sort()                                               # Sort the Dedupelicated list 
                cntedTags[tagGrp]["Total"] = len(colTags[tagGrp])               # Saves totals for tag group to group sub dictionary value
                for tag in tagsSorted:                                          # For each of the tags in the sorted list
                    # Count occurrences of tag in collection and append to list
                    tagCnt = colTags[tagGrp].count(tag)
                    # Append tag to cntedTags dictionary
                    cntedTags[tagGrp][tag] = tagCnt
            else: 
                continue
        return cntedTags

# Creates objects for each rom in the target archive
class romFile(): 
    romFiles = []
    def __init__(romFile, fileName, pArchive, loc):
        m.dv(locals(), "fileName", "pArchive", "loc")
        romFile.name = fileName
        romFile.parent = pArchive
        romFile.location = loc
        romFile.region = []
        romFile.language = []
        romFile.infoTags = []
        romFile.srtRegion = ""
        romFile.tags  = { }
        romFile.romFiles.append(fileName)
    
    # Takes the full file name of the current working file, scrapes it for tags and returns those tags
    def scrape(romFile):
        m.sb("Gathering tags...")
        romFile.tags = re.findall(r'\((?=[^(]*\))(.*?)\)', romFile.name)            # Scrape file name for all occurrences of (***) matching only complete (***)
        for tag in romFile.tags:                                                    # For each of the collected tags
            tagSplit = tag.split(',')                                               # Split the tags on commas
            for splitTag in tagSplit:                                               # For each of the individual tags
                splitTag = splitTag.strip()                                         # Strip whitespace
                if "+" in splitTag:
                    splitTag = splitTag.split('+')
                    tagSplit.extend(splitTag)
                    continue
                else:
                    if splitTag in rArch.romRegions:                    # If the tag can be found in the regions list
                        romFile.region.append(splitTag)           # Add it to the regionTags list
                    elif splitTag in rArch.romLang:                     # If the tag can be found in the Language list
                        romFile.language.append(splitTag)         # Add it to the languageTags list
                    else:                                               # Else if the tag cannot be matched
                        if re.findall(r'PAL.*', splitTag):              # >>>> NEED TO DO THIS BETTER REGEX
                            romFile.region.append("PAL")
                        else:
                            romFile.infoTags.append(splitTag)     # Add it to the miscTags list
        romTags = { "unSrted": romFile.tags, "regionTags": romFile.region, 
                               "languageTags": romFile.language, "miscTags": romFile.infoTags }
        m.sb("Tags are:", ' '.join(romTags["unSrted"])) 
        return romTags
        
    # Takes a given romFile and its scraped tags and sorts it into one of the sort regions
    # Returns either the sort region or 1 for unmatched.
    def sort(romFile, rom, romTags):
        m.sb("Sorting rom...")
        # Attempt to match by region  
        if romTags["regionTags"]:                                            # If regionTags dictionary entry is not empty
            for tag in romTags["regionTags"]:
                if "USA" in romTags["regionTags"]:                             # Attempt to bail out early by matching on master sort region
                    m.ma(rom, "USA")
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
                            m.ma(rom, "USA")
                            return "USA"
                        else:
                            return "World"
                    else:
                        if "PAL" in romTags["regionTags"]:
                            return "Europe"
                        else:
                            return "USA"
                # We werent able to bail out
                if tag in rArch.romRegion["USA"]:
                    if not romTags["languageTags"] or "En" in romTags["languageTags"]:
                        return "USA"
                    else:
                        return "World"
                elif tag in rArch.romRegion["Japan"]:
                        return "Japan"
                elif tag in rArch.romRegion["Europe"]:
                    return "Europe"
                elif tag in rArch.romRegion["World"]:
                    return "World"
                elif tag in rArch.romRegion["EurWor"]:
                    if "En" in romTags["languageTags"]:
                        return "Europe"
                    else:
                        return "World"
                else:
                    continue
        # If no region tags, but has language tags
        elif romTags["languageTags"]:
            if "En" in romTags["languageTags"]:
                # Regionless rom with En language
                #m.sb("Regionless rom with En Tags"
                return "USA"
            elif "Ja" in romTags["languageTags"]:
                # Regionless rom with Ja language
                return "Japan"
            else:
                # Regionless rom with any other language
                return "World"
        else:
            # If no region tags or language tags
            return "UnKwn"
        # Any other case return unknown
        return "UnKwn"
        
    # Moves Roms to sort folders
    def move(romFile, extPath, srtRomDest, srtFolder, homeRgn, moveRomRom):            
        m.dv(locals(), "extPath", "srtRomDest", "srtFolder", "homeRgn", "moveRomRom")
        shutil.move(extPath + "/" + moveRomRom,  srtRomDest + moveRomRom)
        m.mv(moveRomRom, srtFolder)
        return 0

def auditLog(outDest, zipFile, romList, romTotals, relVers, noAudit):
    m.dv(locals(), "outDest", "zipFile", "romTotals", "relVers", "noAudit")
    if not noAudit:
        # Determine what the audit log file will be named
        if relVers:
            auditFn = "[ " + relVers + " No-Intro Set ]"
        else:
            auditFn = "[ " + zipFile + " No-Intro Set ]"
            
        # Processes audit log buffers and writes them to a file in the extraction directory
        auditFPath = outDest + "/" + auditFn        # NEED TO FIX THIS IT WILL CAUSE PROBLEMS IN PRETEND MODE
        if os.path.isfile(auditFPath):              # IN PRETEND WRITE TO PWD OR ARCHIVE DIR
            os.remove(auditFPath)
        auditFile = open(auditFPath, "a")

        m.st("Saving Audit Log to", auditFPath + "...")
        # Write the audit log header information
        auditFile.write("No Effort No Intro" + '\n')
        auditFile.write("   Audit Log" + '\n\n')
        auditFile.write("Created on:    " + exeTime + '\n')
        auditFile.write("Processed:     " + zipFile + '\n')
        auditFile.write("Processed to:  " + outDest + '\n')
        auditFile.write("Total Files:   " + str(romTotals["Total"]) + '\n\n')

        # Process the log buffer and write it to the audit file
        # Writes the collected tags and totals to file:
        # romTotals > Tags > regionTags > tagTotals  
        #rom totals is:  'Tags': {'Total': 6, 
        #'regionTags': {'regionTags': 2, 'tagTotals': [['Japan', 'USA'], [1, 1]]}, 'languageTags': {'languageTags': 5, 'tagTotals': [['De', 'En', 'Fr', 'Ja'], [1, 1, 1, 1]]}, 'miscTags': {'miscTags': 3, 'tagTotals': [['Beta', 'proto', 'test'], [1, 1, 1]]}}}

        # Writes the section header to the file
        auditFile.write("### " + str(romTotals["Tags"]["Total"]) + " Tags Were Scraped From File Names  ###" + '\n')
        # Iterates through each of the tag groups in the romTotals tag dictionary
        for tagGrp in list(romTotals["Tags"])[1:]:
            # Writes the headers with the total for each of the groups
            if tagGrp == "regionTags":
                auditFile.write(str(romTotals["Tags"][tagGrp]["Total"]).rjust(6, ' ') + " Region Tags" + '\n')
            elif tagGrp == "languageTags":
                auditFile.write(str(romTotals["Tags"][tagGrp]["Total"]).rjust(6, ' ') + " Language Tags" + '\n')
            elif tagGrp == "miscTags":
                auditFile.write(str(romTotals["Tags"][tagGrp]["Total"]).rjust(6, ' ') + " Miscellaneous Tags" + '\n')
            # For each of the tags in the respective tag groups dictionary, skipping the first key
            for tag in list(romTotals["Tags"][tagGrp])[1:]:
                # Write the count for each tag to the file, right justified to 6 places to the audit file line
                auditFile.write(str(romTotals["Tags"][tagGrp][tag]).rjust(6, ' ') + " " + str(tag) + '\n')
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
    else:
        m.n("Skipping Audit File Write as Requested...")

class msg():
    class c:
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

    def __init__(msg, debug, verbose):
        if not verbose:
            msg.sb = msg.msgPass
            msg.ma = msg.msgPass
            msg.mv = msg.msgPass
            msg.lf = msg.msgPass
            msg.wk = msg.msgPass
        if debug:
            from dbug import dbmsg
            msg.ds = dbmsg.ds
            msg.dp = dbmsg.dp
            msg.dv = dbmsg.dv
            msg.de = dbmsg.de
    
    # Prints a preformed message to the console
    def say(msg, *line):
        print(' '.join(line))

    # Forms status messages
    # msg.st( message )
    def status(msg, *stMsg):
        msg.say("NeNI:", ' '.join(stMsg))
    # Shorthand alias for method
    st = status

    # Forms sub-status messages
    # msg.sb( message )
    def substatus(msg, *sstMsg):
        msg.say("NeNI:  ", ' '.join(sstMsg))
    # Shorthand alias for method
    sb = substatus
    
    # Forms informational notices
    # m.n( message )
    def notice(msg, *nMsg):
        msg.say("NeNI:", msg.c.yb + "NOTICE:", msg.c.o + ' '.join(nMsg))
    # Shorthand alias for method
    n = notice
    
    # Forms non-fatal warning notices
    # m.wn( message )
    def warning(msg, *wnMsg):
        msg.say("NeNI:", msg.c.yb + "WARNING:", msg.c.o + ' '.join(wnMsg))
    # Shorthand alias for method
    wn = warning
    
    # Forms Error Messages and gives advice to resolve
    # m.er([ erMsg, anything, erAdv ]) > " NeNI: ERROR: errorMessage " and " NeNI:   >>> resolveAdvice "
    def error(msg, *erMsg):
        msg.say("NeNI:", msg.c.rb + "ERROR:", msg.c.o + ' '.join(erMsg) )
    # Shorthand alias for method
    er = error
    
    # Forms informational sub error messages
    # m.ei(message)
    def errorInfo(msg, *erInfo):
        msg.say("NeNI:", msg.c.rb + "ERROR:", msg.c.o + "   >>>", ' '.join(erInfo))
    # Shorthand alias for method
    ei = errorInfo
    
    # Forms messages to notify user of current working file
    # m.wk(rom_file_name)
    def working(msg, wkRom):
        msg.say("NeNI:   Working on Rom", msg.c.cb+ wkRom, msg.c.o)
    # Shorthand alias for method
    wk = working
        
    # Forms messages to notify user of file matches
    # m.mv(romName, moveLocation) > " NeNi: Moved: romName to moveLocation "
    def matched(msg, maRom, maLoc):
        msg.say("NeNI:   Rom", msg.c.cb + maRom, msg.c.o + "Matched", msg.c.yb + maLoc, msg.c.o)
    # Shorthand alias for method
    ma = matched       
    
    # Forms messages to notify user of file moves
    # m.mv(romName, moveLocation) > " NeNi: Moved: romName to moveLocation "
    def move(msg, mvRom, mvLoc):
        msg.say("NeNI:   Moved", msg.c.cb + mvRom, msg.c.o + "to:", msg.c.yb + mvLoc, msg.c.o)
    # Shorthand alias for method
    mv = move
    
    def left(msg, lfRom):
        msg.say("NeNI:   Left", msg.c.cb + lfRom, msg.c.o + "in", msg.c.yb + "Root Directory", msg.c.o)
    # Shorthand alias for method
    lf = left
    
    # Forms an Exit Message
    # exit( "exit description" )
    def exit(msg, exType):
        msg.say("NeNI: Exiting on", str(exType) + "...")
    # Shorthand alias for method
    ex = exit
    
    # Skips debug messages when debug is not enabled
    def msgPass(msg, *line):
        pass
    # Shorthand alias for debug methods
    ds = msgPass
    dp = msgPass
    dv = msgPass
    de = msgPass

# Defines the order subroutines are executed
def mainRoutine():
    global m
    
    # Get arguments
    flags = argParser()
    # Initialize the msg engine
    m = msg(flags.debug, flags.verbose)
    m.dv(locals(), "flags")
    # Performs sanity checks on target file, initializes target archive object
    roms = rArch( checkZip(flags) )
    # Processes roms based on region and/or language and sorts them into groups
    mvFile = roms.processRoms(flags.extTo, flags.outDest, flags.pretend, flags.skip_extraction)
     # Moves rom files to sort folders
    moveRom(mvFile, roms.extPath, roms.outDest, roms.zipPath, roms.romList, flags.homeRgn, flags.pretend)
    # Writes audit log to file
    auditLog(roms.outDest, roms.zipFile, roms.romList, roms.totals, flags.relVers, flags.audit)
    m.ex("Successful Completion")
    sys.exit(0)
	
# Calls the main routine on script startup
mainRoutine()               # Script entry point; execution begins here
