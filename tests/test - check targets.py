import os
import sys
import shutil
from pathlib import Path
from collections import deque
from collections import defaultdict
from dataclasses import dataclass, field
from typing import ClassVar
import zipfile
#from neni import chkTargets as check_targets
from messenger import messenger
m = messenger(debug=True, verbose=True)

# Configuration
testLocation  = "tmp/checktargets_test/" # testLocation must have trailing /
testResources = "tests/checktarget_testcases/checktargets_test"

# Setup the test envrioment in testLocation
def setupEnv():
    shutil.copytree(testResources, testLocation, dirs_exist_ok=True)
class TargetNotFound(Exception):
        pass


def chkTargets(targets, sXtrct, msg):    
    m = msg
    tgtList = [ ]

    class TargetNotFound(Exception):
        pass
    
    @dataclass
    class _target:
        name:           str = field(init=False)                         # The directory name
        path:           Path                                            # The resolved path to the starget
        archives:       set = field(default_factory=set, init=False)    # List of all archives found in target directory
        total:          int  = 0                                        # Total archives found in target directory
        skipExtraction: bool = field(default=False, init=False)         # Marks if this target was processed in skipextract mode
        processed:      bool = field(default=False, init=False)         # Marks if this target has been processed
        hasArchives:    bool = field(default=False, init=False)         # Marks if this target had any archives
        instances: ClassVar[dict] = { }                                 # Dictionary containing all instances of this dataclass
        
        def __post_init__(tgt):
            tgt.__class__.instances[str(tgt.path)] = tgt
            tgt.name = tgt.path.name
        
        def __repr__(tgt):
            return (f"\n_target:"
                    f"\n  name:        {tgt.name}"
                    f"\n  path:        {tgt.path}"
                    f"\n  archives:    {tgt.archives}"
                    f"\n  total:       {tgt.total}"
                    f"\n  sXtrct:      {tgt.skipExtraction}"
                    f"\n  hasArchives: {tgt.hasArchives}"
                    f"\n  processed:   {tgt.processed}")
        
        # Save archive path objects to target object for use in main
        def add(tgt, archive):
            tgt.archives.add(archive)
            tgt.total += 1

    _target.instances.clear()
    
    # Gather a list of all directories in target
    def _gatherDirs(tgtObj, sXtrct):
        # Check that we have permission to access the subtarget
        if not os.access(tgtObj.path, os.R_OK):
            raise PermissionError (f"No Permissions for target: {tgtObj.path}")
        # Iterate through the target directory note directoires found
        for _d in tgtObj.path.iterdir():
            # Check that we have permission to access the subtarget
            if not os.access(_d, os.R_OK):
                raise PermissionError (f"No Permissions for target: {_d.resolve()}")
            if _d.is_dir():
                if str(_d.resolve()) not in tgtObj.instances:
                    # Create a list of any directories in the subtarget
                    _tgtObj = _target(path=_d.resolve())
                    if sXtrct:
                        _tgtObj.skipExtraction = True
            else:
                continue
        return tgtObj
        
    # Gather a list of all archives in target directory
    # Takes a list of target objects
    # Outputs a dictionary in formation { path, targetObj}
    def _gatherArchives(tgtObj):            
        # Iterate through all target objects
        for _tgtObj in list(tgtObj.instances.values()):
            _zipList = [ ]
            # Create a list of any archives in the subtarget
            _zipList.extend( [ _a for _a in _tgtObj.path.glob('*.zip', case_sensitive=None) ] )
            # Iterate through the archives found to validate them for addition to list
            for _z in _zipList:
                # Validate the target
                try:
                    _validateTarget(_z)
                    # If there isn't a target object already created
                    # Create it, add the archive to the obj, and add obj to dict 
                    if _z.resolve() not in _tgtObj.archives:
                        _tgtObj.add(_z.resolve())
                    _tgtObj.hasArchives = True
                except (PermissionError, ValueError) as e:
                    m.er(str(e))
                    m.ei("Please verify this is a valid archive file")
                    continue
        _tgtObj.processed = True

        if not any(t.hasArchives for t in tgtObj.instances.values()):
            raise TargetNotFound(f"Could not find a valid target archive in {tgtObj.path}")
        # Return the populated target objects
        return tgtObj.instances
    
    # Validates a target to prepare it for romArchive
    def _validateTarget(target):
        # Check that we have permission to access the target
        if not os.access(target, os.R_OK):
            raise PermissionError (f"No Permissions for target: {target.resolve()}")
        # Check that the archive has a filesize more than minimum
        if target.stat().st_size <= 22:
            raise ValueError (f"Not a valid file: {target.resolve()}, Filesize: {target.stat().st_size}B") 
        # Test to ensure that file gathered are actually archives
        # For performance, just check the magic bytes
        with open(target, 'rb') as t:
            if not t.read(4) == b'\x50\x4b\x03\x04':
                raise ValueError (f"Failed archive validation: {target.resolve()}") 
        # Target is a valid archive, add it to the target list
        return True

    m.st("Checking target(s)...")

    for target in targets:
        target = Path(target)
        
        try:
            if target.is_dir():
                if str(target.resolve()) not in _target.instances:
                    tgtObj = _target(path=target.resolve())
                else:
                    tgtObj = _target.instances[str(target.resolve())]
                _gatherDirs(tgtObj, sXtrct=sXtrct)
                _gatherArchives(tgtObj)
                tgtObj.processed = True
            elif target.is_file():
                if _validateTarget(target):
                    if str(target.parent.resolve()) not in _target.instances:
                        tgtObj = _target(path=target.parent.resolve())
                        tgtObj.add(target.resolve())
                    else:
                        tgtObj = _target.instances[str(target.parent.resolve())]
                        tgtObj.add(target.resolve())
                    tgtObj.hasArchives = True
                tgtObj.processed   = True
            # Raise if the target exists, but isn't a file or directory
            else:
                raise ValueError (f"Not a valid target: {target.resolve()}")
        except PermissionError as e:
                m.er("Permission Error: Cannot Access", str(target.resolve()))
                m.ei("Please verify you have permissions to access this file")
        except ValueError as e:
                m.er(str(e))
                m.ei("Please verify this is a valid archive file")   
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


############### TESTS BEGIN HERE #################
##### TEST HELPER FUNCTION ####
def dumpTargets(tgtList):
    print(f"\n--- chkTargets returned {len(tgtList)} target(s) ---")
    for key, tgt in tgtList.items():
        print(f"  key: {key}")
        print(f"  tgt: {tgt}")
    print("---")


def assertTargets(tgtList, expected, checkTotal=False):
    assert len(tgtList) == len(expected), (
        f"Target count mismatch\n"
        f"Returned: {len(tgtList)}\n"
        f"Expected: {len(expected)}\n"
        f"Returned keys: {list(tgtList.keys())}")

    for exp in expected:
        key      = str(Path(exp["path"]).resolve())
        archives = exp["archives"] if isinstance(exp["archives"], list) else [exp["archives"]]
        archives = {Path(a).resolve() for a in archives}

        assert key in tgtList, (
            f"Path not found in results\n"
            f"Expected:  {key}\n"
            f"Returned:  {list(tgtList.keys())}")

        tgt             = tgtList[key]
        returnedArchives = {a.resolve() for a in tgt.archives}

        assert returnedArchives == archives, (
            f"Archives mismatch for {key}\n"
            f"Returned:  {returnedArchives}\n"
            f"Expected:  {archives}")

        if checkTotal:
            assert tgt.total == exp.get("total", len(archives)), (
                f"Total mismatch for {key}\n"
                f"Returned:  {tgt.total}\n"
                f"Expected:  {exp.get('total', len(archives))}")


# Defines the order tests will be executed in
# Comment out a test to skip it
def tests():
    singleArchive()                    # Tests normal logic path
    multiArchive()                     # Tests more than one set targeted
    directoryWithSets()                # Tests multi-target logic path
    multiDirectoryWithSets()           # Tests multiple targets containing sets
    multiDirectoryAndArchives()          #
    multiDirectoryBeforeArchives()     # Tests multiple directories and multiple archives being called
    ###--->directoryEmpty()                   # Tests if called on directory with no archives
    #directoryWithJunkAndSets()         # Tests if irrelevant files are being ignored
    #directoryWithGames()               # Tests skip extraction mode
    #multiDirectoryWithGames()          # Tests targeting parent of multiple extracted sets
    #directoryWithBadGame()             # Tests skip extract if there is a bad file
    #directoryWithBadGamesPermissions() # Tests a permissions error with a file in skip extract mode
    #directoryWithBadPermsSXstrct()     # Tests a directory with bad permissions in skip extract mode
    #directoryEmptyXStrct()             # Tests if called on an empty directory in skip extract mode                 
    #archiveWithBadPermissions()        # Tests hanlding of archives neni can't access
    #directoryWithBadPermissions()      # Tests handling a target direcory with bad permissions
    #archiveWithSmallSize()             # Tests if one bad archive spoils the bunch
    #oneBadArchive()                    # Tests handling of a bad archive mixed in with good
    #oneBadArchivePermissions()         # Tests a multiarchive target, one of which has bad perms

# Simulates a single archive being targeted
# chkTargets should return a list with the single arhive
def singleArchive():
    m.st("\nBegining Test singleArchive")
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With 3 Top Level Games (Normal Set).zip" ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to check against
    { "path":       Path(testLocation),
      "archives": [ Path(testLocation, "Archive - With 3 Top Level Games (Normal Set).zip") ],
      "total": 1 
    }, ], checkTotal=True)
    m.st("Test completed Sucessfully")
    
# Simulates a multiple archives being targeted
# chkTargets should return a list with the archives
def multiArchive():
    m.st("\nBegining Test multiArchive")
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}Archive - With 3 Top Level Games (Normal Set)2.zip",
                 f"{testLocation}Archive - With 3 Top Level Games (Normal Set)3.zip" ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    assert len(tgtList) == 1
    # Compile list in output format to check against
    dumpTargets(tgtList)
    assertTargets(tgtList, [
    { "path":       Path(testLocation),
      "archives": [ Path(testLocation, "Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 }, 
    ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates a directory with sets being targeted
# chkTargets should return a list with the arhives found in the directory
def directoryWithSets():
    m.st("\nBegining Test directoryWithSets")
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    { "path":       Path(testLocation, "directory_with_sets"),
      "archives": [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 },
    ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates targeting multiple directories with archive sets
# chkTargets should return a list with the archives
def multiDirectoryWithSets():
    m.st("\nBegining Test multiDirectoryWithSets")
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets",
                 f"{testLocation}directory_with_junk_and_sets" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 2
    assertTargets(tgtList, [
    { "path":       Path(testLocation, "directory_with_sets").resolve(),
      "archives": [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve(), 
                    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve(), 
                    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve() ],
      "total": 3
    },
    { "path":       Path(testLocation, "directory_with_junk_and_sets"),
      "archives": [ Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set).zip"), 
                    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"), 
                    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    } ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates a multiple directories with archives being targeted
# chkTargets should return a list with the archives
def multiDirectoryAndArchives():
    m.st("\nBegining Test multiDirectoryAndArchives")
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                 f"{testLocation}directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set)3.zip",
                 f"{testLocation}directory_with_directories_with sets/directory1",
                 f"{testLocation}directory_with_directories_with sets/directory2" ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 3
    assertTargets(tgtList, [
    # Results to test against
    { "path":       Path(testLocation, "directory_with_directories_with sets"),
      "archives": [ Path(testLocation, "directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    },
    { "path":       Path(testLocation, "directory_with_directories_with sets/directory1"),
      "archives": [ Path(testLocation, "directory_with_directories_with sets/directory1/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with sets/directory1/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with sets/directory1/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    },{ "path":     Path(testLocation, "directory_with_directories_with sets/directory2"),
      "archives": [ Path(testLocation, "directory_with_directories_with sets/directory2/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with sets/directory2/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with sets/directory2/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    } ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates a directories being targted before multiple archives
# chkTargets should return a list with the archives
def multiDirectoryBeforeArchives():
    m.st("\nBegining Test multiDirectoryBeforeArchives")
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_directories_with sets/directory1",
                 f"{testLocation}directory_with_directories_with sets/directory2",
                 f"{testLocation}directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                 f"{testLocation}directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set)3.zip"  ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 3
    assertTargets(tgtList, [
    # Results to test against
    { "path":       Path(testLocation, "directory_with_directories_with sets/directory1"),
      "archives": [ Path(testLocation, "directory_with_directories_with sets/directory1/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with sets/directory1/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with sets/directory1/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    },
    { "path":     Path(testLocation, "directory_with_directories_with sets/directory2"),
      "archives": [ Path(testLocation, "directory_with_directories_with sets/directory2/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with sets/directory2/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with sets/directory2/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    },
    { "path":       Path(testLocation, "directory_with_directories_with sets"),
      "archives": [ Path(testLocation, "directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    } ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates a directory with no archives
# chkTargets should ignore everything and return an empty list
def directoryEmpty():
    m.st("\nBegining Test directoryEmpty")
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Call chkTargets to run the test
    try:
        tgtList  = chkTargets(targets, False, m)
    except TargetNotFound as e:
        print(f"Failed as expected\n Exception: {e}"
        f"\nReturned: Failure TargetNotFound\n"
        f"Expected: Failure TargetNotFound\n" )
    else:
        print(f"\nReturned: No Error\n"
        f"Expected: Failure TargetNotFound\n" )
    finally:
        return

# Simulates a directory with sets being targeted that also has other misc files
# chkTargets should ignore the other files and return a list with the arhives found in the directory
def directoryWithJunkAndSets():
    m.st("\nBegining Test directoryWithJunkAndSets")
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk_and_sets" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":       Path(testLocation, "directory_with_junk_and sets"),
      "archives": [ Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    } ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates skip extraction mode, working on an already extracted set
# chkTargets should return a list of all archives in the directory 
def directoryWithGames():
    m.st("\nBegining Test directoryWithGames")
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_games" ]
    # Compile list in output format to check against
    expected = [ Path(testLocation, "directory_with_games") ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    m.st("Test completed Sucessfully")
    
# Simulates skip extraction mode, targeting parent of multiple already extracted sets
# chkTargets should return a list of all archives in the directory 
def multiDirectoryWithGames():
    m.st("\nBegining Test multiDirectoryWithGames")
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_extracted_sets/directory_with_games",
                 f"{testLocation}directory_with_extracted_sets/directory_with_games2" ]
    # Compile list in output format to check against
    expected = [ Path(testLocation, "directory_with_extracted_sets/directory_with_games"), 
                 Path(testLocation, "directory_with_extracted_sets/directory_with_games2") ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    m.st("Test completed Sucessfully")

# Simulates a directory with a bad zip file in skip extraction mode
# chkTargets should raise and extection and stop
def directoryWithBadGame():
    m.st("\nBegining Test TEdirectoryWithBadGameST")
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk_badfile_and_games" ]
    # Compile list in output format to check against
    # Call chkTargets to run the test
    try:
        tgtList  = chkTargets(targets, True, m)
    except ValueError as e:
        print(f"Failed as expected\n Exception: {e}"
        f"\nReturned: Failure ValueError\n"
        f"Expected: Failure ValueError\n" )
    else:
        print(f"\nReturned: No Error\n"
        f"Expected: Failure ValueError\n" )
    finally:
        return

# Simulates a single archive being targeted that has bad permissions
# chkTargets should raise a PermissionError
def directoryWithBadGamesPermissions():
    m.st("\nBegining Test directoryWithBadGamesPermissions")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "directory_with_games/Fake Game (Vatican) (La).zip", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_games" ]
    # Compile list in output format to check against
    # Call chkTargets to run the test
    try:
        tgtList  = chkTargets(targets, False, m)
    except FileNotFoundError as e:
        print(f"Failed as expected\n Exception: {e}"
        f"\nReturned: Failure FileNotFoundError\n"
        f"Expected: Failure FileNotFoundError\n" )
    else:
        print(f"\nReturned: No Error\n"
        f"Expected: Failure FileNotFoundError\n" )
    finally:
        os.chmod(testLocation + "directory_with_games/Fake Game (Vatican) (La).zip", 0o777)
        return

# Simulates a directory being targeted that has bad permissions
# chkTargets should raise a PermissionError
def directoryWithBadPermsSXstrct():
    m.st("\nBegining Test directoryWithBadPermsSXstrct")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "directory_with_junk", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Compile list in output format to check against
    # Call chkTargets to run the test
    try:
        tgtList  = chkTargets(targets, True, m)
    except TargetNotFound as e:
        print(f"Failed as expected\n Exception: {e}"
        f"\nReturned: Failure TargetNotFound\n"
        f"Expected: Failure TargetNotFound\n" )
    else:
        print(f"\nReturned: No Error\n"
        f"Expected: Failure TargetNotFound\n" )
    finally:
        os.chmod(testLocation + "directory_with_junk", 0o777)
        return
    
# Simulates a directory with no roms in skip extraction mode
# chkTargets should ignore everything and return an empty list
def directoryEmptyXStrct():
    m.st("\nBegining Test directoryEmptyXStrct")
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Compile list in output format to check against
    # Call chkTargets to run the test
    try:
        tgtList  = chkTargets(targets, False, m)
    except TargetNotFound as e:
        print(f"Failed as expected\n Exception: {e}"
        f"\nReturned: Failure TargetNotFound\n"
        f"Expected: Failure TargetNotFound\n" )
    else:
        print(f"\nReturned: No Error\n"
        f"Expected: Failure TargetNotFound\n" )
    finally:
        return

# Simulates a single archive being targeted that has bad permissions
# chkTargets should raise a PermissionError
def archiveWithBadPermissions():
    m.st("\nBegining Test archiveWithBadPermissions")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With Bad Permissions.zip" ]
    # Call chkTargets to run the test
    try:
        tgtList  = chkTargets(targets, False, m)
    except PermissionError as e:
        print(f"Failed as expected\n Exception: {e}"
        f"\nReturned: Failure PermissionError\n"
        f"Expected: Failure PermissionError\n" )
    else:
        print(f"\nReturned: No Error\n"
        f"Expected: Failure PermissionError\n" )
    finally:
        os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o777)
        return

# Simulates a single archive being targeted that has bad permissions
# chkTargets should raise a PermissionError
def directoryWithBadPermissions():
    m.st("\nBegining Test directoryWithBadPermissions")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "directory_with_junk", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Compile list in output format to check against
    # Call chkTargets to run the test
    try:
        tgtList  = chkTargets(targets, False, m)
    except TargetNotFound as e:
        print(f"Failed as expected\n Exception: {e}"
        f"\nReturned: Failure TargetNotFound\n"
        f"Expected: Failure TargetNotFound\n" )
    else:
        print(f"\nReturned: No Error\n"
        f"Expected: Failure TargetNotFound\n" )
    finally:
        os.chmod(testLocation + "directory_with_junk", 0o777)
        return

# Simulates a single invalid archive being targeted
# chkTargets should raise a ValueError
def archiveWithSmallSize():
    m.st("\nBegining Test archiveWithSmallSize")
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With Minimal Filesize.zip" ]
    expected = "Not a valid file: /home/john/.local/tmp/checktargets_test/Archive - With Minimal Filesize.zip, Filesize: 22B"
    # Call chkTargets to run the test
    try:
        tgtList  = chkTargets(targets, False, m)
    except ValueError as e:
        print(f"Failed as expected\n Exception: {e}"
            f"\nReturned: Failure ValueError\n"
            f"Expected: Failure ValueError\n" )
        assert e == expected, (
            f"\nReturned: Failure ValueError\n"
            f"Expected: Failure ValueError\n" )
    else:
        print(f"\nReturned: Failure ValueError\n"
        f"Expected: Failure ValueError\n" )
    finally:
        return

# Simulates a invalid archive mixed in with good archives
# chkTargets return a list excluding the bad file
def oneBadArchive():
    m.st("\nBegining Test oneBadArchive")
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip",
                f"{testLocation}Archive - Thats Not Actually an Archive.zip" ]
    # Compile list in output format to check against
    expected  = [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ]    
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    m.st("Test completed Sucessfully")

# Simulates a invalid archive mixed in with good archives
# chkTargets return a list excluding the bad file
def oneBadArchivePermissions():
    m.st("\nBegining Test oneBadArchivePermissions")
    setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip",
                f"{testLocation}Archive - With Bad Permissions.zip" ]
    # Compile list in output format to check against
    expected  = [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ]    
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o777)
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    m.st("Test completed Sucessfully")

# TODO targeted a non-zip
# TODO nested directories in skip extract
# TODO currupted archive case
# TODO parent with set in sub but also junk in sub
tests()
