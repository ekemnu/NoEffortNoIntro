#####   No Effort No-Intro
#####	John Loreth
#####	2026
#####   0.25
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
#####       0.2x TODO: Added --dat, and the ability to scrape DAT files for file names to test code
#####       0.2x TODO: thread per archive in multi archive workflow
#####       0.2x TODO: better error handling
#####       0.2x TODO: make turf work as expected, make electing a langauge possible
#####       0.2x TODO: simplify count functions
#####       0.2x TODO: better archive process completion verification
#####       0.2x TODO: Per-archive message buffer and messenger thread 

import argparse                 # Used to parse arguments passed to the script at runtime
import sys                      # Used to exit the script
import shutil                   # Used to move and unzip files and archives
from pathlib import Path        # Used to perform os independent path manipulation
from datetime import datetime   # Used to record the date and time script was run
from zipfile import ZipFile
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from messenger import messenger # Used to create terminal status messages during runtime
from archive import romArchive  # User to manage actions of archives

# Gets the arguments passed to the script at invocation
def argParser():
    parser = argparse.ArgumentParser( description='Processes given No-Intro archive(s), sorts by region into sub directories',
                        epilog='Written by John Loreth 2024')
    parser.add_argument('targets', nargs='+')
    parser.add_argument('-a', '--no-audit', action=argparse.BooleanOptionalAction, dest='noAudit',
                        help='Skips writing audit file')
    parser.add_argument('-o', '--output-destination', action='store', nargs='?', dest='outDest',
                        default=None, help='Specifies a directory to output processed roms')
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction,
                        help='Prints debug messages to the console')
    parser.add_argument('-t', '--home-turf', action='store', nargs='?',
                        default='USA', dest='homeRgn', choices=['USA', 'Europe', 'World'],
                        help='Specifies the home sort region (default: USA)')
    parser.add_argument('-p', '--pretend', action=argparse.BooleanOptionalAction, dest='ptend',
                        help='Runs the script without making any changes')
    parser.add_argument('-r', '--release', action='store', dest='relVers',
                        help='Specify No-Intro release information to include after processing')
    #TODO make this for pointing to an already extracted dir of no-intro roms, x implies no o
    parser.add_argument('-x', '--skip-extraction', action=argparse.BooleanOptionalAction, dest='sXtrct',
                        help='Skips extraction of the target archive, looks for a directory with that name to process')
    parser.add_argument('-v', '--verbose', action=argparse.BooleanOptionalAction,
                        help='Prints additional information to the console')
    parser.add_argument('--version', action='version', version='NenI 0.25')
    
    # Store the flags as an object
    flags = parser.parse_args()
    # If the final output destination has been given save absolute path
    if flags.outDest:
        flags.outDest = Path(flags.outDest)
    # Pretend requires sXtract
    if flags.ptend:
        flags.sXtrct = True
    return flags

##### Processes targets specified at runtime
def chkTargets(targets, msg):    
    m = msg
    tgtList = []
    
    m.st("Checking target archive...")
    for target in targets:
        target = Path(target)
        # Check to see if the target is a file or directory
        # Check to see if target is a valid file
        if target.is_file():
            # Target was a file, add it to the target list
            m.de("is file")
            tgtList.append(target.resolve())
            continue
        # If the target wasn't a file, was it a directory?
        elif target.is_dir():
            tgtList.extend([ f for f in target.glob('*.zip', case_sensitive=None) ])
            m.de("is dir")
            # Target is a directory, scan it for archives
            m.st("Gathering Archives From Source Directory...")
            for tgtFile in tgtList:
                m.st("Discovered", tgtFile.name, "in Target Directory")
            continue
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
                        rom.move(zf)

                    finally:
                        thr.extractQueue.task_done()
    futures = []            
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
    # Set the target(s) and returns absolute path(s) and then
    # iterates through all archives that were passed to the script
    for target in chkTargets(flags.targets, m):
        m.st("Working on target archive <", target.name, ">...")
        # Initializes target archive object with user preferences
        archive = romArchive(
            # Stores the full path of the target archive
            target,
            # Sets the user defined processed output destination
            flags.outDest, 
            # Sets the No-Intro release version information about the archive
            flags.relVers,
            # Sets the user defined home region for file sort
            flags.homeRgn, 
            # Sets the pretend flag; process extracted files only, skip move
            flags.ptend, 
            # Skips extraction; use to point at directory full of files
            flags.sXtrct,
            # Skips the creation of the audit file
            flags.noAudit,
            # Messenger
            m,
            # Execeution time TODO: Break out auditfile to it's own thing
            now.strftime("%m/%d/%Y %H:%M:%S")
        )
        # Processes the archive, extracting it, processing the files, and moving it to the final location

        # Gather a list of all files extracted from the target archive
        archive.getFiles()
        # Gather information about the extracted files
        archive.processRoms()
        # Total the files and scraped tags in each category
        archive.cntRoms()
        archive.cntTags()
        # Move the files to the sort regions
        archive.prepMove()
        # Moves the processed archive to output destination
        #archive.move()
        # threaded move
        threader(archive, m)
        # Writes the audit log documenting changes made to final destination
        archive.auditLog()
        # Mark the archive as fully processed
        archive.markProcessed()
        
    # Exit the script after successful processing of all archives and files
    m.ex("Successful Completion")
    sys.exit(0)