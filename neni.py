#####   No Effort No-Intro
#####	John Loreth
#####	2026
#####   0.26
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
#####       0.16 Bug fixes, and improved sorting logic
#####       0.17 Improved exception, file, audit handling, bug fixes
#####       0.18 Further improvements to tag scraping logic
#####       0.19 Rewrote Sort logic
#####       0.20 Split codebase for easier maintainability
#####       0.21 Created tests to exercise scrape and sort logic. Fixed scrape and sort bugs these tests found.
#####       0.22 Refactored romFile() to be a dataclass, scraping logic and romFile performance improvements
#####       0.23 Support reading archive ToC > scrape > sort > extract into place. Bug Fixes
#####       0.24 Parrellalize Rom extraction
#####       0.25 Simplified tag/rom counters by rewriting to use Collections, simplified audit log code, bug fixes
#####       0.26 Rewrote chkTargets to be more flexible and robust, wrote tests to validate, fixed all bugs they fonund
#####       0.2x TODO: Added --dat, and the ability to scrape DAT files for file names to test code
#####       0.2x TODO: thread per archive in multi archive workflow
#####       0.2x TODO: better error handling
#####       0.2x TODO: make turf work as expected, make electing a langauge possible
#####       0.2x TODO: better archive process completion verification
#####       0.2x TODO: Per-archive message buffer and messenger thread 

import argparse                 # Used to parse arguments passed to the script at runtime
import sys                      # Used to exit the script
import shutil
from pathlib import Path        # Used to perform os independent path manipulation
from datetime import datetime   # Used to record the date and time script was run
from zipfile import ZipFile
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from messenger import messenger # Used to create terminal status messages during runtime
from targets import chkTargets
from archive import romArchive  # User to manage actions of archives

# Gets the arguments passed to the script at invocation
def argParser():
    parser = argparse.ArgumentParser( description='Processes given No-Intro archive(s), sorts by region into sub directories',
                        epilog='Written by John Loreth 2026')
    parser.add_argument('targets', nargs='*', default=[ ])
    parser.add_argument('-a', '--noaudit', action=argparse.BooleanOptionalAction, dest='noAudit',
                        help='Skips writing audit file')
    parser.add_argument('-o', '--output-destination', action='store', nargs='?', dest='outDest',
                        default=None, help='Specifies a directory to output processed roms')
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction,
                        help='Prints debug messages to the console')
    parser.add_argument('-t', '--home-turf', action='store', nargs='?',
                        default='USA', dest='homeRgn',
                        help='Specifies the home sort region (default: USA)')
    parser.add_argument('-l', '--language', action='store', nargs='?',
                        default='En', dest='language',
                        help='Specifies the prefered language (default: En)')
    parser.add_argument('-p', '--pretend', action=argparse.BooleanOptionalAction, dest='ptend',
                        help='Runs the script without making any changes')
    parser.add_argument('-r', '--release', action='store', dest='relVers',
                        help='Specify No-Intro release information to include after processing')
    parser.add_argument('-x', '--skip-extraction',  action='append', nargs='?', dest='sXtrct',
                        default=[ ], help='Skips extraction of the target archive, looks for a directory with that name to process')
    parser.add_argument('-v', '--verbose', action=argparse.BooleanOptionalAction,
                        help='Prints additional information to the console')
    parser.add_argument('--version', action='version', version='NenI 0.26')
    
    # Store the flags as an object
    flags = parser.parse_args()

    # Error if no targets or sXtract targets are passed
    if not flags.targets and not flags.sXtrct:
        raise ValueError ("Must specifiy a valid target")
    
    # If the final output destination has been given save absolute path
    if flags.outDest:
        flags.outDest = Path(flags.outDest).resolve()
    
    # Process targets
    resolvedTgts = [ ]
    for target in flags.targets:
        target = Path(target).resolve()
        if not (target.is_file() or target.is_dir()):
            raise ValueError (f"target {target} is not a file or directory")
        resolvedTgts.append(target)
    flags.targets.clear()
    flags.targets = resolvedTgts

    # Process skip extraction targets
    if flags.sXtrct:
        resolvedSXTgts = [ ]
        for sxTarget in flags.sXtrct:
            sxTarget = Path(sxTarget).resolve()
            if not sxTarget.is_file() and not sxTarget.is_dir():
                raise ValueError (f"skip extraction target {sxTarget} not a file or directory")
            resolvedSXTgts.append(sxTarget)
        flags.sXtrct.clear()
        flags.sXtrct = resolvedSXTgts
    
    # Handles home turf region setting
    if flags.homeRgn:
        try:
           rf
        except:
          from rom import romFile as rf
        finally:
            if flags.homeRgn not in rf.romRegions:
                raise ValueError (f"{flags.homeRgn} is not a valid rom region")
    else:
        flags.homeRgn = "USA"
    
    # Handles language preference setting
    if flags.language:
        try:
           rf
        except:
          from rom import romFile as rf
        finally:
            if flags.language not in rf.romLang:
                raise ValueError (f"{flags.language} is not a valid rom language")
    else:
        flags.language = "En"
   
    return flags

def threader(archive, msg):
    ra = archive
    ra.m = msg
    extractQueue = ra.extractQueue

    class extractWorker():
        def __init__(thr, zipFile, extractQueue):
            thr.zipFile      = zipFile
            thr.extractQueue = extractQueue
            
        def run(thr):
            with ZipFile(thr.zipFile) as zf:
                while True:
                    try:
                        rom = thr.extractQueue.get_nowait()
                    except Empty:
                        break

                    try:
                        rom.move(zf, False)

                    finally:
                        thr.extractQueue.task_done()
    
    class moveWorker():
        def __init__(thr, setLoc, extractQueue):
            thr.setLoc       = setLoc
            thr.extractQueue = extractQueue
        def run(thr):
                while True:
                    try:
                        rom = thr.extractQueue.get_nowait()
                    except Empty:
                        break

                    try:
                        rom.move(thr.setLoc, True)

                    finally:
                        thr.extractQueue.task_done()

    futures = []            
    if ra.skipExtract:
        workers = [ moveWorker(ra.zipFPath, extractQueue)
            for _ in range(4) ]
    else:
        workers = [ extractWorker(ra.zipFPath, extractQueue)
                for _ in range(4) ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(worker.run)
            for worker in workers
        ]

        for future in futures:
            future.result()


# Defines the order subroutines are executed
def mainRoutine():
    now = datetime.now()
    # Get arguments passed to script at runtime
    flags = argParser()
    # Initialize the msg engine
    m = messenger(flags.debug, flags.verbose)
    
    # Creates archive objects
    def createArchObj(tgtObj, archive, flags, m, now):
        archObj = romArchive(
            # Stores the target object for the archive
            tgtObj,
            # Stores the resolved path object for the archive
            archive,
            # Sets the user defined processed output destination
            flags.outDest, 
            # Sets the No-Intro release version information about the archive
            flags.relVers,
            # Sets the user defined home region for file sort
            flags.homeRgn, 
            # Sets the pretend flag; process extracted files only, skip move
            flags.ptend,
            # Skips the creation of the audit file
            flags.noAudit, # TODO: Break out auditfile to its own thing
            # Messenger
            m,
            # Execeution time
            now.strftime("%m/%d/%Y %H:%M:%S")
        )
        return archObj
    
    # Gather and validate targets
    try:
        targets = chkTargets(flags.targets, flags.sXtrct, m)
    except ValueError as e:
        print(e)
        
    # iterates through all targets that were passed to the script
    for tgtObj in targets:
        # Skip this target object if no archives were discovered
        if not tgtObj.hasArchives:
            continue
        
        # If skip extraction is enabled for this target
        if tgtObj.skipExtraction:
            m.st("Preparing target directory <", str(tgtObj.path), ">...")
            # Create an archive objet for its parent directory
            archObj = createArchObj(tgtObj, tgtObj.path, flags, m, now)
            # Add the archives dicovered during target check to archive object
            archObj.romList["unSrted"].extend(tgtObj.archives)
            # Process the target, scraping and sorting the files and moving to output location
            archObj.process(threader)
        else:
            # If skip extraction wasnt enabled
            # Iterate through all the archives discovered in the set
            for archive in tgtObj.archives:
                m.st("Preparing target archive <", archive.name, ">...")
                # Creates an archive object for each of the discovered archives
                archObj = createArchObj(tgtObj, archive, flags, m, now)
                # Process the target, scraping and sorting the files and moving to output location
                archObj.process(threader)
    
    # Exit the script after successful processing of all archives and files
    m.ex("Successful Completion")
    sys.exit(0)