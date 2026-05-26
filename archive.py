import sys                      # Used to exit the script
from pathlib import Path        # Used to perform os independent path manipulation
from collections import Counter
from zipfile import ZipFile
from queue import Queue
from rom import romFile


##### Stores information about the rom collection, and performs operations on it
class romArchive():
    ##### Variables that are specific to the instanced object
    def __init__(ra, zipFile, extTo, outDest, relVers, homeRgn, ptend, sXtrct, noAudit, msg, exeTime):
        ra.m         = msg                          # Messenger for writing lines to terminal
        ra.zipFile   = zipFile                      # Stores the full path to the target archive
        ra.zipPath   = zipFile.parent               # Stores the directory in which the target archive is located
        ra.zipFn     = zipFile.name                 # Stores string full name of the target archive
        ra.zipFnRoot = zipFile.stem                 # Stores string with the name of the target archive without extension
        ra.zipFnExt  = zipFile.suffix               # Stores string with the extension of the target archive
        ra.extTo     = extTo                        # Stores a custom location to extract target
        ra.extPath   = extTo.joinpath(ra.zipFnRoot) # Stores the extraction target directory
        ra.outDest   = outDest                      # Stores the final destination of the processed roms
        ra.relVers   = str(relVers)                 # Stores No-Intro release version information
        ra.exeTime   = exeTime                      # Time execution started
        ra.romList = {      # Stores a list of all decompressed files in the extraction directory
                "unSrted": [], "USA": [], "Japan": [], "Europe": [], "World": [], "UnKwn": [] }
        ra.colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] }           # Stores scraped tags
        ra.totals = {"USA": 0, "Japan": 0, "Europe": 0, "World": 0, "UnKwn": 0, "Total": 0, "Tags": { } } # Stores totals
        ra.extractQueue = Queue()
        ra.skipExtract = sXtrct
        ra.pretend = ptend
        ra.homeRgn = homeRgn
        ra.noAudit = noAudit
        ra.processed = False

        if ra.zipFnExt.lower() != ".zip":
            # If the extension is not .zip
            print("Error: Target File is not a Zip Archive")
            print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
            print("         Ex: $ neni /home/user/Downloads/archive.zip")
            quit(1)
        else:
            # If the extension is .zip
            ra.m.st("Processing Archive", ra.zipFn + "....")
            # Handle user output destination flag
            if not ra.outDest:
                # Sets the final destination to be the same as the target archive
                ra.m.wn("Output Destination Not Specified; Using Source Directory")
                ra.m.de("outdest not set")
                ra.outDest = ra.zipPath
        
      
    # Processes the current target archive when called
    def process(ra):
        # Decompress the target archive
        #ra.unzip()
        # Gather a list of all files extracted from the target archive
        ra.getFiles()
        # Gather information about tfrom collections import Counterhe extracted files
        ra.processRoms()
        # Total the files and scraped tags in each category
        ra.cntRoms()
        ra.cntTags()
        # Move the files to the sort regions
        #ra.moveRoms()
        # Moves the processed archive to output destination
        ra.move()
        # Writes the audit log documenting changes made to final destination
        ra.auditLog()
        # Mark the archive as fully processed
        ra.markProcessed()

    def getFiles(ra):        
        ra.m.st("Gathering Files Information From Target Archive...")
        with ZipFile(ra.zipFile) as zf:
            # Get a list of files from the target archive ToC, add to unsorted list, exclude [BIOS] files
            for r in zf.namelist():
                if r.lower().endswith(".zip") and not r.startswith('[BIOS]'):
                    ra.romList["unSrted"].append(r)
        
        if not ra.romList["unSrted"]:
            # If no files were gathered from the extraction path
            ra.m.er("Unable to Retrieve File Information From Target Archive")
            ra.m.ei("No Such File or Directory")
            ra.m.ex("Error")
            sys.exit(1)
        else:
            # Successfully gathered files
            ra.m.sb("Files Gathered")
            return 0
    
    ##### Iterates through all of the files in the extraction directory and attempts to match them to a region
    def processRoms(ra):
        ra.m.st("Processing Roms...")
        # For each of the unsorted rom list
        for rom in ra.romList["unSrted"]:
            # If the file is a archive, and is not a bios
            ra.m.wk(rom)
            # Initialize a new instance of a romFile object
            # Send name of rom, name of parent archive, where it was extracted to
            romObj = romFile(name=rom, parent=ra.zipPath, location=ra.extPath, m=ra.m)
            # Scrape tags from the working rom
            # Collects the tags into the archive
            ra.collectTags(romObj.scrape())
            # Attempts to sort the rom into one of the master sort regions
            romObj.srtRegion = romObj.sort()
            # Stores the rom to the archive by sorted region
            if romObj.srtRegion == "UnKwn":
                # Prints warning message with name of unmatched file
                ra.m.wn("Unable to match", romObj.name)
                # Add rom object to the unknown list
                ra.romList[romObj.srtRegion].append(romObj)
                # Prints debug substatement with location of skipped file
                ra.m.lf(romObj.name)
                # Set the sort location to be the root directory
                romObj.srtLocation = ra.extPath
            else:
                # Prints message with name of matched file and sort region
                ra.m.ma(romObj.name, romObj.srtRegion)
                # Add rom object to the list by sort region
                ra.romList[romObj.srtRegion].append(romObj)
                # Handle user selectable region flag homeRgn
                if ra.homeRgn == romObj.srtRegion:
                    # if sort region is selected region leave in root
                    romObj.srtLocation = ra.extPath
                else:
                    # Set the rom's final location to be a region sort folder
                    romObj.srtLocation = ra.extPath.joinpath(romObj.srtRegion)
            continue
        return 0

    ##### Takes a set of tags and appends to a complete set of tags from the current working archive
    def collectTags(ra, romTags):
        # Iterate through the default tag groups stored in the object
        for tagGrp in ra.colTags:
            # If the group isn't empty
            if romTags[tagGrp]:
                # Append the tag to the object's tag collection
                ra.colTags[tagGrp].extend(romTags[tagGrp])
        return 0
    
    ##### Creates sort directories as needed and moves sorted files into directories
    # Executes the sort list, moving the roms to their sort folders    
    def prepMove(ra):    
        # Creates the sort directories as needed
        def makeDir(outLocation, srtFolder):
            ra.m.sb("Creating folder", srtFolder, "at extraction path...")
            try:
                # Attempt to create the directory
                outLocation.mkdir(exist_ok=True)
            except Exception as e:
                # Exit if error
                ra.m.er("Unable to create sort folder at extraction path", str(e))
                ra.m.ex("error")
                sys.exit(1)
            else:
                # If directory create successfully
                return 0

        # Executes the sort list, moving the roms to their sort folders
        ra.m.st("Moving Sorted Roms ...")
        if not ra.pretend:
            # Iterate through romList groups skipping the unsorted list
            for romGrp in list(ra.romList.keys())[1:]:
                # Only process if group is not empty
                if ra.romList[romGrp]:
                    # Iterate through the romFile registry of object instances
                    for rom in ra.romList[romGrp]:
                        # Save the final location to the rom object
                        rom.outLocation = rom.srtLocation
                        #If the sort directory doesn't exist, create it
                        if not rom.srtLocation.is_dir():
                            makeDir(rom.srtLocation, rom.srtRegion)
                        # move the rom to it's destination
                        ra.extractQueue.put(rom)
                        #if rom.move(ra.zipFile) == 0: # Move the rom and check for success 
                            # If successful move to next rom in list
                        #    continue
                        #else:
                            # Fail if rom move was not successful
                        #    m.er("Failed to move rom to", romGrp)
                        #    m.ex("Error")
                        #    sys.exit(1)
                    # Continue to next rom after processing
                    continue       
        else:
            ra.m.n("Skipping Rom Move Because We're Pretending")
            return 0

    def move(ra):
        if not ra.pretend:
            ra.m.st("Moving Working Directory to Output Destination...")
            # Set the output location
            mvLoc = ra.outDest.joinpath(ra.zipFnRoot)
            # If the output location isn't the same as extraction location
            if mvLoc != ra.extPath:
                # If the output location doesn't exist
                if not ra.outDest.is_dir():
                    # Create the output location
                    ra.outDest.mkdir()
                # Move the working directory to the final destination
                ra.extPath.replace(mvLoc)
                # Set the target archives out destination to the outputed location
                ra.outDest = mvLoc
                # Print message notifying user of successful move
                ra.m.sb("Moved to:", str(ra.outDest))
                return 0
            else:
                 # Skip if extraction and output directory are the same
                 ra.m.sb("Working Extraction Directory and Destination are Identical, Skipping")
                 return 1
        else:
            # Skip if we're pretending
            ra.m.n("Skipping Output Move Because We're Pretending")
            return 0
    
    ##### Counts all the roms in the sorted rom list
    def cntRoms(ra):
        # Create a list of the sort groups
        romGrps = list(ra.romList.keys())[1:]
        # Get the total count of roms in each of the sorted groups
        ra.totals = {g: len(ra.romList[g]) for g in romGrps}
        # Get the grand total for all the roms in the archive
        ra.totals["Total"] = sum(ra.totals.values())
        return 0
    
    ##### Takes a dictionary of collected tags and returns a dictionary with sorted tags, totals 
    # input format: colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] } 
    def cntTags(ra):
        #Format:
        # cntedTags = { "Total": 0, "regionTags": { "regionTags": 0, "tagTotals": [ [], [] ] },
        #                          "languageTags": { "languageTags": 0, "tagTotals": [ [], [] ] },
        #                          "miscTags": { "miscTags": 0, "tagTotals": [ [], [] ] } }
        
        # Gets the length of the unsorted list and saves it as the total tag count
        cntedTags = {"Total": len(ra.colTags["unSrted"])}
        # For each of the sorted tags groups
        for tagGrp in list(ra.colTags.keys())[1:]:
            # Calculate the groups's length
            counts = Counter(ra.colTags[tagGrp])
            # Saves the total for the tag group
            cntedTags[tagGrp] = {"Total": sum(counts.values()), **dict(sorted(counts.items()))}
        # Saves the tag counts to the archive instance
        ra.totals["Tags"] = cntedTags
        return 0

    def cntRomsOLD(ra):
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
        # Save the totals to the archive's object
        ra.totals = auditRomsTotals
        return 0
    
    ##### Takes a dictionary of collected tags and saves a dictionary with sorted tags, totals 
    # input format: colTags = { "unSrted": [], "regionTags" : [], "languageTags" : [], "miscTags" : [] } 
    def cntTagsOLD(ra):
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
                # Deduplicate and sort by using set, saving as a list
                tagsSorted = sorted(set(ra.colTags[tagGrp]))
                # Sort the Deduplicated list 
                #tagsSorted.sort()
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
    
    #### Records actions taken by the script writes them to a file in the output directory
    def auditLog(ra):
        # If no audit flag was not set
        if not ra.noAudit:
            ra.m.st("Writing audit log to output destination...")
            # Determine what the audit log file will be named
            # If release version was specified at runtime, use it
            if ra.relVers:
                ra.auditFn = f"[ {ra.relVers} No-Intro Set ]"
            # If no release information was specified, use the target archive name
            else:
                ra.auditFn = f"[ {ra.zipFnRoot} No-Intro Set ]"
            
            # Set the location to write the audit file
            # If we're pretending, set location to be the same as target file
            if ra.pretend:
                auditFPath = ra.zipPath.joinpath(ra.auditFn)
            # If we're not pretending, set it to the output destination
            else:
                auditFPath = ra.outDest.joinpath(ra.zipFnRoot, ra.auditFn)
            # Check if file already exists
            if auditFPath.is_file():
                # Remove file if it already exists
                auditFPath.unlink()
            # Open the file for writing
            with open(auditFPath, "w") as auditFile:

                ra.m.st("Saving Audit Log to", str(auditFPath) + "...")
                # Write the audit log header information
                auditFile.write(f"No Effort No Intro\n")
                auditFile.write(f"   Audit Log\n\n")
                auditFile.write(f"Created on:    {ra.exeTime}\n")
                auditFile.write(f"Processed:     {ra.zipFile}\n")
                auditFile.write(f"Processed to:  {ra.outDest}\n")
                auditFile.write(f"Total Files:   {ra.totals["Total"]}\n\n")

                # Process the log buffer and write it to the audit file
                # Writes the collected tags and totals to file:
                # romTotals > Tags > regionTags > tagTotals  
                #rom totals is:  'Tags': {'Total': 6, 
                #'regionTags': {'regionTags': 2, 'tagTotals': [['Japan', 'USA'], [1, 1]]}, 'languageTags': {'languageTags': 5, 'tagTotals': [['De', 'En', 'Fr', 'Ja'], [1, 1, 1, 1]]}, 'miscTags': {'miscTags': 3, 'tagTotals': [['Beta', 'proto', 'test'], [1, 1, 1]]}}}

                # Writes the section header to the file
                auditFile.write(f"### {ra.totals["Tags"]["Total"]} Tags Were Scraped From File Names  ###\n")
                # Iterates through each of the tag groups in the romTotals tag dictionary
                for tagGrp in list(ra.totals["Tags"])[1:]:
                    # Writes the headers with the total for each of the groups
                    if tagGrp == "regionTags":
                        auditFile.write(f"{str(ra.totals["Tags"][tagGrp]["Total"]).rjust(6, ' ')} Region Tags\n")
                    elif tagGrp == "languageTags":
                        auditFile.write(f"{str(ra.totals["Tags"][tagGrp]["Total"]).rjust(6, ' ')}  Language Tags\n")
                    elif tagGrp == "miscTags":
                        auditFile.write(f"{str(ra.totals["Tags"][tagGrp]["Total"]).rjust(6, ' ')}  Miscellaneous Tags\n")
                    # For each of the tags in the respective tag groups dictionary, skipping the first key
                    for tag in list(ra.totals["Tags"][tagGrp])[1:]:
                        # Write the count for each tag to the file, right justified to 6 places to the audit file line
                        auditFile.write(f"{str(ra.totals["Tags"][tagGrp][tag]).rjust(6, ' ')}  {str(tag)}\n")
                    # Add blank line at end of list for formatting  
                    auditFile.write(f"\n")
                    continue

                # Writes the results of the rom sort
                for srtGrp in list(ra.romList.keys())[1:]:
                    if ra.romList[srtGrp]:
                        if srtGrp == "UnKwn":
                            auditFile.write(f"###  {str(ra.totals[srtGrp])} Files Were Unmatched  ###\n")
                        else:
                            auditFile.write(f"###  {str(ra.totals[srtGrp])} Files Matched the {str(srtGrp)} Region  ###\n")

                        for logLn in ra.romList[srtGrp]:
                            auditFile.write(f"{str(logLn.name)}\n")
                    else:
                        auditFile.write(f"\n")
                        continue
                    auditFile.write(f"\n")
        else:
            ra.m.n("Skipping Audit File Write as Requested...")
        
    # Marks the current working archive as processed
    def markProcessed(ra):
        # TODO: Actually make this do checks to ensure data was gathered correctly
        ra.processed = True