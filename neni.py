#####   No Effort No-Intro
#####	John Loreth
#####	2024
#####   0.15
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
#####       0.15 Better error handling, transitioned from os to pathlib for better path handling

import argparse                 # Used to parse arguments passed to the script at runtime
import sys                      # Used to exit the script
import os
import shutil                   # Used to move and unzip files and archives
import re                       # Used to perform regex searches
from pathlib import path        # Used to perform path manipulation
from itertools import chain     # Used to combine dictionary values into a list
from datetime import datetime   # Used to record the date and time script was run

global exeTime

now = datetime.now()
exeTime = now.strftime("%m/%d/%Y %H:%M:%S")

# Gets the arguments passed to the script at invocation
def argParser():
    parser = argparse.ArgumentParser( description='Processes given No-Intro archive, sorts by region into sub directories',
                        epilog='Written by John Loreth 2024')
    parser.add_argument('targets', nargs='+')
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
    parser.add_argument('--version', action='version', version='NenI 0.15')
    
    flags = parser.parse_args()
    return flags

##### Processes targets specified at runtime
def chkTargets(targets):    
    print("targets")
    tgtList = []
    
    m.st("Checking target archive...")
    m.dv(locals(), "targets")
    for target in targets:
        # Check to see if the target is a file or directory
        # Check to see if target is a valid file
        if os.path.isfile(target):
            # Target was a file, add it to the target list
            m.de("is file")
            tgtList.append(os.path.abspath(target))
            continue
        # If the target wasn't a file, was it a directory?
        elif os.path.isdir(target):
            m.de("is dir")
            # Target is a directory, scan it for archives
            m.st("Gathering Archives From Source Directory...")
            for tgtFile in os.listdir(target):
                if tgtFile.endswith(".zip"):
                    m.st("Discovered", tgtFile, "in Target Directory")
                    # Save the absolute path to the target to the target list
                    tgtList.append(os.path.abspath(tgtFile))
                    continue
                else:
                    # If the scanned file was not an archive, skip it
                    continue
            # Return the list of full paths to the targets
            if not tgtList:
                m.er("No Archives Were Discovered in", target)
                m.ex("Error")
                sys.exit(1)
            else:
                m.st("Target Directory Scanned Gathered")
                return tgtList
        else:
            # Error if the target was neither a file or directory
            m.er("Target File or Directory Cannot Be Found")
            m.ei("Please supply a valid path to either a single, or a directory with No-Intro archives and run NeNi again")
            m.ei("  Ex: $ neni /home/user/Downloads/archive.zip")
            m.ei("  or: $ neni /home/user/Downloads/NoIntroArchives")
            m.ex("Error")
            sys.exit(1)
    # Return the list of full paths to the targets
    return tgtList
            
##### Stores information about the rom collection, and performs operations on it
class romArchive():
    # Variables that are shared with all new objects in class    


    ##### Variables that are specific to the instanced object
    def __init__(ra, zipFile, extTo, outDest, relVers, homeRgn, ptend, sXtrct, noAudit):
        ra.zipFile   = zipFile      # Stores the full path to the target archive
        ra.zipPath   = ""           # Stores the directory in which the target archive is located
        ra.zipFn     = ""           # Stores the full name of the target archive
        ra.zipFnRoot = ""           # Stores the name of the target archive without extension
        ra.zipFnExt  = ""           # Stores the extension of the target archive
        ra.extPath   = ""           # Stores the extraction target directory
        ra.extTo     = extTo
        ra.outDest   = outDest      # Stores the final destination of the processed roms
        ra.relVers   = relVers
        ra.romList = {              # Stores a list of all decompressed files in the extraction directory
                "unSrted": [], "USA": [], "Japan": [], "Europe": [], "World": [], "UnKwn": [] }
        ra.colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] }           # Stores scraped tags
        ra.totals = {"USA": 0, "Japan": 0, "Europe": 0, "World": 0, "UnKwn": 0, "Total": 0, "Tags": { } } # Stores totals
        ra.skipExtract = sXtrct
        ra.pretend = ptend
        ra.homeRgn = homeRgn
        ra.noAudit = noAudit
        ra.processed = False
        
    # Returns a list of functions to iterate through and execute
    def __iter__(ra):
        return iter([
        # Gather information about the target archive
        ra.inspect(),
        #unzip the target archive
        ra.unzip(),
        # Gather a list of all files extracted from the target archive
        ra.getFiles(),
        # Gather information about the extracted files
        ra.processRoms(),
        # Total the files and scraped tags in each category
        ra.cntRoms(),
        ra.cntTags(),
        # Move the files to the sort regions
        ra.moveRoms(),
        # Moves the processed archive to output destination
        ra.move(),
        # Writes the audit log documenting changes made to final destination
        ra.auditLog(),
        # Mark the archive as fully processed
        ra.markProcessed()
    ])
        
    # Iterates through all of the files in the extraction directory and attempts to match them to a region
    def processRoms(ra):
        m.st("Processing Roms...")
        # For each of the unsorted rom list
        for rom in ra.romList["unSrted"]:e
            # If the file is a archive, and is not a bios
            if rom.endswith(".zip") and '[BIOS]' not in rom:
                m.wk(rom)
                # Initialize a new instance of a romFile object
                # Send name of rom, name of parent archive, where it was extracted to
                romObj = romFile(rom, ra.zipPath, ra.extPath)
                m.dv(locals(), "romObj")
                #m.dv(locals(), "romFiles")
                # Scrape tags from the working rom
                # Collects the tags into the archive
                ra.collectTags(romObj.scrape())
                #m.dv(locals(), "romTags", "ra.colTags")
                # Attempts to sort the rom into one of the master sort regions
                romObj.sort()
                # Stores the rom to the archive by sorted region
                if romObj.srtRegion == "UnKwn":
                    # Prints warning message with name of unmatched file
                    m.wn("Unable to match", rom)
                    # Add rom object to the unknown list
                    ra.romList[romObj.srtRegion].append(romObj)
                    # Set the final location to be the root directory
                    romObj.srtLocation = "/"
                    # Prints debug substatement with location of skipped file
                    m.lf(rom)
                else:
                    # Prints message with name of matched file and sort region
                    m.ma(romObj.name, romObj.srtRegion)
                    # Add rom object to the list by sort region
                    ra.romList[romObj.srtRegion].append(romObj)
                    # Handle user selectable region flag homeRgn
                    if ra.homeRgn == romObj.srtRegion:
                        # if sort region is selected region leave in root
                        romObj.srtLocation = "/"
                    else:
                        # Set the rom's final location to be a region sort folder
                        romObj.srtLocation = "/" + romObj.srtRegion
                continue
            else:
                continue
        # get totals of roms and tags after processing
        m.dv(locals(), "rom")
        return 0
    
    ##### Gathers information about the target archive
    def inspect(ra):
        # Get the path and complete name of the zip passed to script
        ra.zipPath, ra.zipFn = os.path.split(ra.zipFile)
        # Get the base file name and extension from file name  
        ra.zipFnRoot, ra.zipFnExt = os.path.splitext(ra.zipFn) 
        # Gets the target directory for file extraction from zip name
        ra.extPath = os.path.join(ra.extTo, ra.zipFnRoot)
        # Check if the archive has a .zip extension 
        if not ra.zipFn.endswith(".zip"):
            # If the extension is not .zip
            print("Error: Target File is no a Zip Archive")
            print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
            print("         Ex: $ neni /home/user/Downloads/archive.zip")
            quit(1)
        else:
            # If the extension is .zip
            m.st("Processing Archive", ra.zipFn + "....")
            # Handle user output destination flag
            if not ra.outDest:
                # Sets the final destination to be the same as the target archive
                m.de("outdest not set")
                ra.outDest = ra.zipPath
            return 0
    
    ##### Unzips the target archive
    def unzip(ra):
        m.de("unzip")
        # If neither pretend nor skip extraction are enabled
        if not ra.pretend and not ra.skipExtract:
            m.st("Checking Extraction Directory...", ra.extPath)
            # Check if extraction directory already exists
            if not os.path.isdir(ra.extPath):
                m.st("Decompressing Archive...")
                try: 
                    # Decompress the archive to the extraction destination
                    shutil.unpack_archive(ra.zipFile, ra.extPath, "zip")
                except:
                    # If the decompress returned an error
                    m.er("Archive Decompression Failed")
                    m.ex("Error")
                    sys.exit(1)
                else:
                    # Successfully decompressed
                    m.st("Successfully Decompressed", ra.zipFile, "to:", ra.extPath)
                    return 0
            else:
                # Exit with error if the decompression target directory already exists
                m.er("Decompression Target Directory Already Exists")
                m.ex("Error")
                sys.exit(1)
        else:
            # Skip decompression if pretend enabled
            m.n("Skipping Decompression Because We're Pretending")
            return 0
    
    ##### Gets a list, and iterates through all roms in the extraction path
    def getFiles(ra):
        m.st("Gathering Files From Extraction Target Directory...")
        # Get a list of files from the extraction dir and add to unsorted list
        ra.romList["unSrted"] = os.listdir(ra.extPath)
        if not ra.romList["unSrted"]:
            # If no files were gathered from the extraction path
            m.er("Unable to Process Extracted Files")
            m.ei("No Such File or Directory")
            m.ex("Error")
            sys.exit(1)
        else:
            # Successfully gathered files
            m.sb("Files Gathered")
            return 0
    
    ##### Takes a set of tags and appends to a complete set of tags from the current working archive
    def collectTags(ra, romTags):
        # Iterate through the default tag groups stored in the object
        for tagGrp in ra.colTags:
            # If the group isn't empty
            if ra.colTags[tagGrp]:
                # Iterate through each of the tags in the object's default tag groups
                for tag in romTags[tagGrp]:
                    # Append the tag to the object's tag collection
                    ra.colTags[tagGrp].append(tag)
        return 0
    
    ##### Creates sort directories as needed and moves sorted files into directories
    def moveRoms(ra):
        # Creates the sort directories as needed
        def makeDir(outLocation, srtFolder):
            m.sb("Making folder", srtFolder, "at extraction path")
            os.mkdir(outLocation)

        # Executes the sort list, moving the roms to their sort folders
        #m.dv(locals(), "romList")
        m.st("Moving Sorted Roms ...")
        #print(mvFiles, type(mvFiles))
        if not ra.pretend:
            # Iterate through romList groups skipping the unsorted list
            for romGrp in list(ra.romList.keys())[1:]:
                # Only process if group is not empty
                if ra.romList[romGrp]:
                    # Iterate through the romFile registry of object instances
                    for rom in ra.romList[romGrp]:
                        # Save the final location to the rom object
                        rom.outLocation = ra.extPath + rom.srtLocation
                        # If the sort directory doesn't exist, create it
                        if not os.path.isdir(rom.outLocation):
                            makeDir(rom.outLocation, rom.srtRegion)
                        # move the rom to it's destination
                        if rom.move() == 0: # Move the rom and check for success 
                             # If successful move to next rom in list
                            continue
                        else:
                            # Fail if rom move was not successful
                            m.er("Failed to move rom to", moveRomGrp)
                            m.ex("Error")
                            sys.exit(1)
                    # Continue to next rom after processing
                    continue       
        else:
            m.n("Skipping Rom Move Because We're Pretending")
            return 0
    
    # Moves the fully processed archive from the extraction directory to final destination
    def move(ra):
        if not ra.pretend:
            m.st("Moving Working Directory to Output Destination...")
            # Move the working directory to the final destination
            if ra.outDest != ra.extPath:
                ra.outDest = ra.outDest + "/" + ra.zipFnRoot
                #m.dv(locals(), "ra.outDest", )
                shutil.move(ra.extPath, ra.outDest)
                return 0
            else:
                 m.sb("Working Extraction Directory and Destination are Identical, Skipping")
                 return 1
        else:
            m.n("Skipping Output Move Because We're Pretending")
            return 0
    
    # Counts all the roms in the rom list
    def cntRoms(ra):
        # Create a temporary list to hold the rom counts
        auditRomsCnted = []                                         
        # Get a count of roms on each of the sort lists
        for cntRomGrp in list(ra.romList.keys())[1:]:           # For each sort groups, skipping the unsorted list
            auditRomsCnted.append(cntRomGrp)                    # Add the sort group label to the list
            auditRomsCnted.append(len(ra.romList[cntRomGrp]))   # count the items and add it after the label
        # Create a dictionary to save the counts
        # the first and every other as keys, second and every other as values
        auditRomsTotals = { grp:ttl for (grp,ttl) in zip(auditRomsCnted[::2], auditRomsCnted[1::2])}   
        # Save the total number of roms        
        auditRomsTotals["Total"] = sum(auditRomsCnted[1::2])
        m.dv(locals(), "auditRomsTotals")
        # Save the totals to the archive's object
        ra.totals = auditRomsTotals
        return 0
    
    ##### Takes a dictionary of collected tags and returns a dictionary with sorted tags, totals 
    # input format: colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] } 
    def cntTags(ra):
        #m.dv(locals(), "colTags")
        # Format:
        # cntedTags = { "Total": 0, "regionTags": { "regionTags": 0, "tagTotals": [ [], [] ] },
        #                          "languageTags": { "languageTags": 0, "tagTotals": [ [], [] ] },
        #                          "miscTags": { "miscTags": 0, "tagTotals": [ [], [] ] } }

        cntedTags = { "Total": 0, "regionTags": { "Total": 0 }, "languageTags": { "Total": 0 }, "miscTags": { "Total": 0 } }
        cntedTags["Total"] = len(ra.colTags["unSrted"])                # Get the total number of tags scraped from all files
        
        ##### Iterate through the collected tags, totaling them
        # For each of the categories, skipping the first
        for tagGrp in list(ra.colTags.keys())[1:]:
            # Check if the group has any tags
            if ra.colTags[tagGrp]:
                # Deduplicate by using set, saving as a list
                tagsSorted = list(set(ra.colTags[tagGrp]))
                # Sort the Deduplicated list 
                tagsSorted.sort()
                # Saves totals for current tag group to sub dictionary value
                cntedTags[tagGrp]["Total"] = len(ra.colTags[tagGrp])
                # For each of the tags in the sorted list
                for tag in tagsSorted:
                    # Count occurrences of tag in collection and append to list
                    tagCnt = ra.colTags[tagGrp].count(tag)
                    # Append tag to cntedTags dictionary
                    cntedTags[tagGrp][tag] = tagCnt
            # Skip if tag group has no tags
            else: 
                continue
        # Save the tag totals so the archive's object
        ra.totals["Tags"] = cntedTags
        return 0

    def auditLog(ra):
        #m.dv(locals(), "ra.outDest", "ra.zipFile", "ra.totals", "ra.relVers", "ra.noAudit")
        if not ra.noAudit:
            m.st("Writing audit log to output destination...")
            # Determine what the audit log file will be named
            if ra.relVers:
                auditFn = "[ " + ra.relVers + " No-Intro Set ]"
            else:
                ra.auditFn = "[ " + ra.zipFile + " No-Intro Set ]"
                
            # Processes audit log buffers and writes them to a file in the extraction directory
            auditFPath = ra.outDest + "/" + auditFn     # NEED TO FIX THIS IT WILL CAUSE PROBLEMS IN PRETEND MODE
            if os.path.isfile(auditFPath):              # IN PRETEND WRITE TO PWD OR ARCHIVE DIR
                os.remove(auditFPath)
            auditFile = open(auditFPath, "a")

            m.st("Saving Audit Log to", auditFPath + "...")
            # Write the audit log header information
            auditFile.write("No Effort No Intro" + '\n')
            auditFile.write("   Audit Log" + '\n\n')
            auditFile.write("Created on:    " + exeTime + '\n')
            auditFile.write("Processed:     " + ra.zipFile + '\n')
            auditFile.write("Processed to:  " + ra.outDest + '\n')
            auditFile.write("Total Files:   " + str(ra.totals["Total"]) + '\n\n')

            # Process the log buffer and write it to the audit file
            # Writes the collected tags and totals to file:
            # romTotals > Tags > regionTags > tagTotals  
            #rom totals is:  'Tags': {'Total': 6, 
            #'regionTags': {'regionTags': 2, 'tagTotals': [['Japan', 'USA'], [1, 1]]}, 'languageTags': {'languageTags': 5, 'tagTotals': [['De', 'En', 'Fr', 'Ja'], [1, 1, 1, 1]]}, 'miscTags': {'miscTags': 3, 'tagTotals': [['Beta', 'proto', 'test'], [1, 1, 1]]}}}

            # Writes the section header to the file
            auditFile.write("### " + str(ra.totals["Tags"]["Total"]) + " Tags Were Scraped From File Names  ###" + '\n')
            # Iterates through each of the tag groups in the romTotals tag dictionary
            for tagGrp in list(ra.totals["Tags"])[1:]:
                # Writes the headers with the total for each of the groups
                if tagGrp == "regionTags":
                    auditFile.write(str(ra.totals["Tags"][tagGrp]["Total"]).rjust(6, ' ') + " Region Tags" + '\n')
                elif tagGrp == "languageTags":
                    auditFile.write(str(ra.totals["Tags"][tagGrp]["Total"]).rjust(6, ' ') + " Language Tags" + '\n')
                elif tagGrp == "miscTags":
                    auditFile.write(str(ra.totals["Tags"][tagGrp]["Total"]).rjust(6, ' ') + " Miscellaneous Tags" + '\n')
                # For each of the tags in the respective tag groups dictionary, skipping the first key
                for tag in list(ra.totals["Tags"][tagGrp])[1:]:
                    # Write the count for each tag to the file, right justified to 6 places to the audit file line
                    auditFile.write(str(ra.totals["Tags"][tagGrp][tag]).rjust(6, ' ') + " " + str(tag) + '\n')
                # Add blank line at end of list for formatting  
                auditFile.write('\n')
                continue

            # Writes the results of the rom sort
            #for srtGrp in list(ra.romList)[1:]:
            for srtGrp in list(ra.romList.keys())[1:]:
                if ra.romList[srtGrp]:
                    if srtGrp == "UnKwn":
                        auditFile.write("###  " + str(ra.totals[srtGrp]) + " Files Were Unmatched  ###" + '\n')
                    else:
                        auditFile.write("###  " + str(ra.totals[srtGrp]) + " Files Matched the " + str(srtGrp) + " Region  ###" + '\n')

                    for logLn in ra.romList[srtGrp]:
                        auditFile.write(str(logLn) + '\n')
                else:
                    auditFile.write('\n')
                    continue
                auditFile.write('\n')
            auditFile.close()
        else:
            m.n("Skipping Audit File Write as Requested...")
        
    # Marks the current working archive as processed
    def markProcessed(ra):
        # Actually make this do checks to ensure data was gathered correctly
        ra.processed = True

##### Skeleton object for each rom in the target archive
class romFile():
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
    
    def __init__(rf, fileName, pArchive, extPath):
        m.dv(locals(), "fileName", "pArchive", "extPath")
        rf.name = fileName                  # File name of the file
        rf.path = extPath + "/" + fileName  # Stores full path to file
        rf.parent = pArchive                # Parent archive the file was extracted from
        rf.location = extPath               # Stores in what directory the file is located
        rf.srtLocation = ""                 # Directory relative to root ext dir to which the file should be moved
        rf.outLocation = ""                 # Final location of sorted rom
        rf.region = []                      # Region(s) as scraped from file's tags
        rf.language = []                    # Language(s) as scraped from the file's tags
        rf.infoTags = []                    # Misc tag(s) scraped from the file's tags
        rf.srtRegion = ""                   # Stores sort region determined by the sort method
        rf.tags  = { }                      # Stores a list of all the tags from the scrape method

    # Takes the full file name of the current working file, scrapes it for tags and returns those tags
    def scrape(rf):
        m.sb("Gathering tags...")
        rf.tags = re.findall(r'\((?=[^(]*\))(.*?)\)', rf.name)            # Scrape file name for all occurrences of (***) matching only complete (***)
        for tag in rf.tags:                                               # For each of the collected tags
            tagSplit = tag.split(',')                                     # Split the tags on commas
            for splitTag in tagSplit:                                     # For each of the individual tags
                splitTag = splitTag.strip()                               # Strip whitespace
                if "+" in splitTag:
                    splitTag = splitTag.split('+')
                    tagSplit.extend(splitTag)
                    continue
                else:
                    if splitTag in rf.romRegions:    # If the tag can be found in the regions list
                        rf.region.append(splitTag)           # Add it to the regionTags list
                    elif splitTag in rf.romLang:                     # If the tag can be found in the Language list
                        rf.language.append(splitTag)         # Add it to the languageTags list
                    else:                                               # Else if the tag cannot be matched
                        if re.findall(r'PAL.*', splitTag):              # >>>> NEED TO DO THIS BETTER REGEX
                            rf.region.append("PAL")
                        else:
                            rf.infoTags.append(splitTag)     # Add it to the miscTags list
        rf.tags = { "unSrted": rf.tags, "regionTags": rf.region, 
                               "languageTags": rf.language, "miscTags": rf.infoTags }
        m.sb("Tags are:", ' '.join(rf.tags["unSrted"])) 
        return rf.tags
        
    # Takes a given romFile and its scraped tags and sorts it into one of the sort regions
    # Returns either the sort region or 1 for unmatched.
    def sort(rf):
        m.sb("Sorting rom...")
        # Attempt to match by region  
        if rf.tags["regionTags"]:                                            # If regionTags dictionary entry is not empty
            for tag in rf.tags["regionTags"]:
                if "USA" in rf.tags["regionTags"]:                             # Attempt to bail out early by matching on master sort region
                    rf.srtRegion =  "USA"
                elif tag == "Japan":
                    if len(rf.tags["regionTags"]) == 1:
                        rf.srtRegion =  "Japan"
                    elif rf.tags["regionTags"][1] in rf.romRegion.keys(): 
                        if rf.romTags["languageTags"][0] != "Ja":
                            continue
                        else:
                            rf.srtRegion =  "Japan"
                    else:
                        rf.srtRegion =  "Japan"
                elif tag == "Europe":
                    rf.srtRegion =  "Europe"
                elif tag == "World":
                    if len(rf.tags["regionTags"]) == 1:
                        if not rf.tags["languageTags"] or "En" in rf.tags["languageTags"]:
                            rf.srtRegion =  "USA"
                        else:
                            rf.srtRegion =  "World"
                    else:
                        if "PAL" in rf.tags["regionTags"]:
                            rf.srtRegion =  "Europe"
                        else:
                            rf.srtRegion =  "USA"
                # We werent able to bail out
                if tag in rf.romRegion["USA"]:
                    if not rf.tags["languageTags"] or "En" in rf.tags["languageTags"]:
                        rf.srtRegion =  "USA"
                    else:
                        rf.srtRegion =  "World"
                elif tag in rf.romRegion["Japan"]:
                        rf.srtRegion =  "Japan"
                elif tag in rf.romRegion["Europe"]:
                    rf.srtRegion =  "Europe"
                elif tag in rf.romRegion["World"]:
                    rf.srtRegion =  "World"
                elif tag in rf.romRegion["EurWor"]:
                    if "En" in rf.tags["languageTags"]:
                        rf.srtRegion =  "Europe"
                    else:
                        rf.srtRegion =  "World"
                else:
                    continue
        # If no region tags, but has language tags
        elif rf.tags["languageTags"]:
            if "En" in rf.tags["languageTags"]:
                # Regionless rom with En language
                #m.sb("Regionless rom with En Tags"
                rf.srtRegion =  "USA"
            elif "Ja" in rf.tags["languageTags"]:
                # Regionless rom with Ja language
                rf.srtRegion =  "Japan"
            else:
                # Regionless rom with any other language
                rf.srtRegion =  "World"
        else:
            # If no region tags or language tags
            rf.srtRegion =  "UnKwn"
        return
        
    # Moves Rom to sort folder
    def move(rf):
        shutil.move(rf.path, rf.outLocation + "/" + rf.name)
        m.mv(rf.name, rf.srtRegion)
        return 0

class messenger():
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
        msg.say("NeNI: Working on Rom", msg.c.cb+ wkRom, msg.c.o)
    # Shorthand alias for method
    wk = working
        
    # Forms messages to notify user of file matches
    # m.mv(romName, moveLocation) > " NeNi: Moved: romName to moveLocation "
    def matched(msg, maRom, maLoc):
        msg.say("NeNI: Rom", msg.c.cb + maRom, msg.c.o + "Matched", msg.c.yb + maLoc, msg.c.o)
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
    
    # Get arguments passed to script at runtime
    flags = argParser()
    # Initialize the msg engine
    m = messenger(flags.debug, flags.verbose)
    m.dv(locals(), "flags")
    # Set the target(s) and returns absolute path(s) and then
    # iterates through all archives that were passed to the script
    for target in chkTargets(flags.targets):
        m.st("Working on target archive", target, "...")
        # Initializes target archive object with user preferences
        archive = romArchive(
            # Stores the full path of the target archive
            target,
            # Stores the user defined extraction location
            flags.extTo,
            # Sets the user defined processed output destination
            flags.outDest, 
            # Sets the No-Intro release version information about the archive
            flags.relVers,
            # Sets the user defined home region for file sort
            flags.homeRgn, 
            # Sets the pretend flag; process extracted files only, skip move
            flags.pretend, 
            # Skips extraction; use to point at directory full of files
            flags.skip_extraction,
            # Skips the creation of the audit file
            flags.audit
        )
        # Processes the archive, extracting it, processing the files, and moving it to the final location
        [ processStep for processStep in archive ]
    # Exit the script after successful processing of all archives and files
    m.ex("Successful Completion")
    sys.exit(0)
	
# Calls the main routine on script startup
mainRoutine()               # Script entry point; execution begins here
