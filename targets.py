import os                                   # Used to check target premissions
from pathlib import Path                    # Used to handle target filesystem paths
from collections import deque               # Used to handle target queue
from dataclasses import dataclass, field    # Used for target objects
from typing import ClassVar                 # Used for target objects

@dataclass
class _target:
    name:           str  = field(init=False)                        # The directory name
    path:           Path                                            # The resolved path to the starget
    archives:       set  = field(default_factory=set, init=False)   # List of all archives found in target directory
    invalidFiles:   list = field(default_factory=list, init=False)  # List of invalid files encountered
    unprocessed:    list = field(default_factory=list, init=False)  # List of unprocessed file found while scraping dirs
    total:          int  = 0                                        # Total archives found in target directory
    skipExtraction: bool = field(default=False)                     # Marks if this target was processed in skipextract mode
    isProcessed:    bool = field(default=False, init=False)         # Marks if this target has been processed
    hasArchives:    bool = field(default=False, init=False)         # Marks if this target had any archives
    instances:      ClassVar[dict] = { }                            # Dictionary containing all instances of this dataclass
    
    # Create registry of target object instances
    # Add new objects on creatoin
    def __post_init__(tgt):
        tgt.__class__.instances[str(tgt.path)] = tgt
        tgt.name = tgt.path.name
    
    # Outputs status of target object for debugging
    def __repr__(tgt):
        return ( f"\n_target:"
                 f"\n  name:         {tgt.name}"
                 f"\n  path:         {tgt.path}"
                 f"\n  archives:     {tgt.archives}"
                 f"\n  invalidFiles: {tgt.invalidFiles}"
                 f"\n  unprocessed:  {tgt.unprocessed}"
                 f"\n  total:        {tgt.total}"
                 f"\n  sXtrct:       {tgt.skipExtraction}"
                 f"\n  hasArchives:  {tgt.hasArchives}"
                 f"\n  isProcessed:  {tgt.isProcessed}" )
    
    # Return the archives list for literation
    def __iter__(tgt):
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
    targets = [ targets, sXtrct ]
    tgtList = [ ]

    class TargetNotFound(Exception):
        pass

    _target.instances.clear()
    
    # Takes a targetobject specified at runtime and processes it
    # Recursively adds directories to be scanned, adds archives to tgtObj
    def _gatherTargets(tgtObj, sXtrct):
        _tgtList = deque()
        _tgtList.append(tgtObj)

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
                tgtObj.isProcessed = True
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
                    tgtObj.isProcessed = True

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
    for _i, _tL in enumerate(targets):
        for target in _tL: 
            # If we're processing the skip extract list, set sXtrct to TRUE
            setSXtrct = (_i == 1)
            # If the passed target is a dir, check if there is already an instance
            # If there is an instance, use it, if not create one
            if target.is_dir():
                if str(target) not in _target.instances:
                    tgtO = _target(path=target, skipExtraction=setSXtrct)
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
                    tgtO = _target(path=_resdParent, skipExtraction=setSXtrct)
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
            if not tgtObj.isProcessed:
                _gatherTargets(tgtObj, setSXtrct)
        except PermissionError as e:
                m.er("Permission Error: Cannot Access", str(tgtObj.path))
                m.ei("Please verify you have permissions to access this file")
                tgtObj.isProcessed = True
                continue
        except ValueError as e:
                m.er(str(e))
                m.ei("Please verify this is a valid archive file")
                tgtObj.isProcessed = True
                continue
        except TargetNotFound as e:
                m.er(str(e))
                m.ei("Please verify the target")
                m.st("Continuting to next target")
                tgtObj.isProcessed = True
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
    return _target.instances.values()