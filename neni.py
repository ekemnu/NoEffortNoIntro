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
#####       0.26
#####       0.2x TODO: Added --dat, and the ability to scrape DAT files for file names to test code
#####       0.2x TODO: thread per archive in multi archive workflow
#####       0.2x TODO: better error handling
#####       0.2x TODO: make turf work as expected, make electing a langauge possible
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
    parser.add_argument('-a', '--noaudit', action=argparse.BooleanOptionalAction, dest='noAudit',
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
    parser.add_argument('--version', action='version', version='NenI 0.26')
    
    # Store the flags as an object
    flags = parser.parse_args()
    # If the final output destination has been given save absolute path
    if flags.outDest:
        flags.outDest = Path(flags.outDest)
    # Pretend requires sXtract
    if flags.ptend:
        flags.sXtrct = True
    return flags

import os
from pathlib import Path
from collections import deque
from dataclasses import dataclass, field
from typing import ClassVar

@dataclass
class _target:
    name:           str  = field(init=False)                        # The directory name
    path:           Path                                            # The resolved path to the starget
    archives:       set  = field(default_factory=set, init=False)   # List of all archives found in target directory
    invalidFiles:   list = field(default_factory=list, init=False)  # List of invalid files encountered
    unprocessed:    list = field(default_factory=list, init=False)  # List of unprocessed file found while scraping dirs
    total:          int  = 0                                        # Total archives found in target directory
    skipExtraction: bool = field(default=False)                     # Marks if this target was processed in skipextract mode
    processed:      bool = field(default=False, init=False)         # Marks if this target has been processed
    hasArchives:    bool = field(default=False, init=False)         # Marks if this target had any archives
    instances: ClassVar[dict] = { }                                 # Dictionary containing all instances of this dataclass
    
    # Create registry of target object instances
    # Add new objects on creatoin
    def __post_init__(tgt):
        tgt.__class__.instances[str(tgt.path)] = tgt
        tgt.name = tgt.path.name
    
    # Outputs status of target object for debugging
    def __repr__(tgt):
        return (f"\n_target:"
                f"\n  name:         {tgt.name}"
                f"\n  path:         {tgt.path}"
                f"\n  archives:     {tgt.archives}"
                f"\n  invalidFiles: {tgt.invalidFiles}"
                f"\n  total:        {tgt.total}"
                f"\n  sXtrct:       {tgt.skipExtraction}"
                f"\n  hasArchives:  {tgt.hasArchives}"
                f"\n  processed:    {tgt.processed}")
    
    # Return the archives list for literation
    def __iter__(tgt):
        # TODO have this remove the invalid files from the list before iteration
        return iter(tgt.archives)
    
    # Save archive path objects to target object for use in main
    def add(tgt, archive):
        tgt.archives.add(archive)
        tgt.total = len(tgt.archives)

    # Adds a discovered archive to the unprocessed list for processing
    def unprocAdd(tgt, archive):
        tgt.unprocessed.append(archive)
    
    # Save archive path objects to target object for use in main
    def invalid(tgt, archive):
        tgt.invalidFiles.append(archive)
    
    # Checks if the target object has archive paths associated with it
    def hasArchs(tgt):
        if tgt.archives:
            tgt.hasArchives = True
        return True if tgt.hasArchives else False


def chkTargets(targets, sXtrct, msg):    
    m = msg
    tgtList = [ ]

    class TargetNotFound(Exception):
        pass

    _target.instances.clear()
    
    # Takes a targetobject specified at runtime and processes it
    # Recursively adds directories to be scanned, adds archives to tgtObj
    def _gatherTargets(tgtObj, sXtrct):
        _tgtList = deque()
        _tgtList.append(tgtObj)
        _procList = [ ]

        # TODO make resursive directory scan only 2 levels deep
        while _tgtList:
            tgtObj = _tgtList.popleft()
            # If the target objet has not unprocessed files, assume it was a passed directory
            if not tgtObj.unprocessed:
                 # Check that we have permission to access the target
                if not os.access(tgtObj.path, os.R_OK):
                    raise PermissionError (f"No Permissions for target: {tgtObj.path}")
                # Iterate through the target objet directory
                # Scraped directories become target obejcts, archives get added to parent tgtobj
                for _t in tgtObj.path.iterdir():
                    # Check that we have permission to access the subtarget
                    try:
                        if not os.access(_t, os.R_OK):
                            raise PermissionError (f"No Permissions for target: {_t.resolve()}")
                    except PermissionError as e:
                        m.er("Permission Error: Cannot Access", str(_t.resolve()))
                        m.ei("Please verify you have permissions to access this file")
                        tgtObj.invalid(_t.resolve())
                        continue
                    # If the scraped target is a directory create a tgtObject for it
                    if _t.is_dir():
                        _resT = _t.resolve()
                        if str(_resT) not in tgtObj.instances:
                            # create target object for the subtarget if none exists
                            _tgtObj = _target(path=_resT, skipExtraction=sXtrct)
                        else:
                            # If a tgtObj for the subtarget exists, use it
                            _tgtObj = _target.instances[str(_resT)]
                        # Add subTgtObj to target list to loop back and hit unprocessed branch
                        _tgtList.append(_tgtObj)
                        continue
                    if _t.is_file() and _t.suffix.lower() == ".zip":
                        # Add it to the unprecessed list for this tgtObj
                        tgtObj.unprocessed.append(_t.resolve())
                if tgtObj.unprocessed:
                    _tgtList.append(tgtObj)
                    continue
                tgtObj.processed = True
            # If the tgtObj unprocessed list is populated
            # This catches anything found in the above scan, or archives passed as targets
            if tgtObj.unprocessed:
                    # For each of the files in the unprocessed list
                    for _z in tgtObj.unprocessed:
                        # Validate the file to be a valid target archive
                        try:
                            _validateTarget(_z)
                            _resZ = _z.resolve()
                            # If the archive is not already in tgtObj archives list, add it
                            if _resZ not in tgtObj.archives:
                                tgtObj.add(_resZ)
                        except (PermissionError, ValueError) as e:
                            m.er(str(e))
                            m.ei("Please verify this is a valid archive file")
                            # If an error occurs for the file add it to tgtObj's invalid file list
                            tgtObj.invalid(_z.resolve())
                            continue
                    # Check to see if the tgtObj archives list is populated
                    tgtObj.hasArchs()
                    # Mark the tgtObj as having been processed
                    tgtObj.processed = True

    # Validates a target to prepare it for romArchive
    def _validateTarget(archive):
        # Check that we have permission to access the target
        if not os.access(archive, os.R_OK):
            raise PermissionError (f"No Permissions for target: {archive.resolve()}")
        # Check that the archive has a filesize more than minimum
        if archive.stat().st_size <= 22:
            raise ValueError (f"Not a valid file: {archive.resolve()}, Filesize: {archive.stat().st_size}B") 
        # Test to ensure that file gathered are actually archives
        # For performance, just check the magic bytes
        with open(archive, 'rb') as t:
            if not t.read(4) == b'\x50\x4b\x03\x04':
                raise ValueError (f"Failed archive validation: {archive.resolve()}") 
        # Target is a valid archive, add it to the target sXtrctlist
        return True

    m.st("Checking target(s)...")

    # Create target objets from target(s) passed at runtime
    for target in targets:
        # Get the resolved path to the target
        target = Path(target).resolve()
        
        # If the passed target is a dir, check if there is already an instance
        # If there is an instance, use it, if not create one
        if target.is_dir():
            if str(target) not in _target.instances:
                tgtO = _target(path=target, skipExtraction=sXtrct)
            else:
                tgtO = _target.instances[str(target)]
            # If the passed directory isn't in the target processing queue, add it
            if tgtO not in tgtList:
                tgtList.append(tgtO)
        # If the passed target is a file, check if there is already a parent instance
        # If there is a object instance for the parent directory, use it, if not create one
        if target.is_file():
            _resdParent = target.parent.resolve()
            if str(_resdParent) not in _target.instances:
                tgtO = _target(path=_resdParent, skipExtraction=sXtrct)
            else:
                tgtO = _target.instances[str(_resdParent)]
            # Add the processed passed archive to the object unprocessed list for _gatherTargets
            tgtO.unprocAdd(target)
            # If the tgtObj isn't already in the target queue, add it
            if tgtO not in tgtList:
                tgtList.append(tgtO)
    
    # Processes tgtOBjects, scanning for archives within it and its subdirectories
    for tgtObj in tgtList:
        try:
            # If the target hasn't already been processed, process it
            if not tgtObj.processed:
                _gatherTargets(tgtObj, sXtrct)
        except PermissionError as e:
                m.er("Permission Error: Cannot Access", str(tgtObj.path))
                m.ei("Please verify you have permissions to access this file")
                tgtObj.processed = True
                continue
        except ValueError as e:
                m.er(str(e))
                m.ei("Please verify this is a valid archive file")   
                continue
        except TargetNotFound as e:
                m.er(str(e))
                m.ei("Please verify the target")
                m.st("Continuting to next target")
                continue
    
    ### TODO let neni deal with this
    #if not _target.instances.values():
        # Error if no archives could be found
    #    m.er("Unable To Find Valid Target(s)")
    #    m.ei("Please supply a valid path to either a single archive, or a directory with No-Intro archives and run NeNi again")
    #    m.ei("  Ex: $ neni /home/user/Downloads/archive.zip")
    #    m.ei("  or: $ neni /home/user/Downloads/NoIntroArchives")
    #    m.ex("Error")
    #   raise TargetNotFound (f"target not found")
    
    # Return the list of full paths to the targets
    return _target.instances

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
    
    ### TODO to match new chkTargets, save a set of romArchives that have been created and only create if not a duplicate
    ###      if there is a duplicate archive, add it to the romlist instead, again checking for duplicates
    ###      this will skip getting files twice when in skip extraction mode
    
    for target in chkTargets(flags.targets, flags.sXtrct, m):
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