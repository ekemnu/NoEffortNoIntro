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
from targets import chkTargets, _target
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

# Defines the order tests will be executed in
# Comment out a test to skip it
def tests():
    singleArchive()                    # Tests normal logic path
    multiArchive()                     # Tests more than one set targeted
    directoryWithSets()                # Tests multi-target logic path
    directoryWithSymlinks()            # Tests targeting a directory containing symlinks
    multiDirectoryWithSets()           # Tests multiple targets containing sets
    multiDirectoryAndArchives()        # Tests targeting multiple directories and multiple archives
    multiDirectoryBeforeArchives()     # Tests multiple directories and multiple archives being called
    directoryEmpty()                   # Tests if called on directory with no archives
    directoryWithJunkAndSets()         # Tests if irrelevant files are being ignored
    directoryWithGames()               # Tests skip extraction mode
    multiDirectoryWithGames()          # Tests targeting parent of multiple extracted sets
    directoryWithBadGame()             # Tests skip extract if there is a bad file
    directoryWithBadGamesPermissions() # Tests a permissions error with a file in skip extract mode
    directoryWithBadPermsSXstrct()     # Tests a directory with bad permissions in skip extract mode
    directoryEmptyXStrct()             # Tests if called on an empty directory in skip extract mode                 
    directoryWithBadPermissions()      # Tests handling a target direcory with bad permissions
    archiveWithBadPermissions()        # Tests hanlding of archives neni can't access
    archiveWithAPasswprd()             # Tests handling of a password protected archive
    archiveWithSmallSize()             # Tests if one bad archive spoils the bunch
    archiveWithLongName()              # Tests targeting an archive with a very long name
    archiveWithUnicode()               # Tests targeting a archive with uniode in name
    archiveSameTwice()                 # Tests targeting the same archive twice
    oneBadArchive()                    # Tests handling of a bad archive mixed in with good
    oneBadArchivePermissions()         # Tests a multiarchive target, one of which has bad perms
    noTarget()                         # Tests targeting nothing
    badTarget()                        # Tests targeting a non-archive
    badTargetSys()                     # Tests targeting a system file

############### TESTS BEGIN HERE #################
##### TEST HELPER FUNCTION ####
def dumpTargets(tgtList):
    print(f"\n--- chkTargets returned {len(tgtList)} target(s) ---")
    for key, tgt in tgtList.items():
        print(f"  key: {key}")
        print(f"  tgt: {tgt}")
    print("---")

def assertTargets(tgtList, expected, checkTotal=False, checkSXtrct=False, checkArchives=False, checkInvalidFiles=False):
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

        tgt              = tgtList[key]
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

        if checkSXtrct:
            assert tgt.skipExtraction == exp.get("sXtrct", False), (
                f"skipExtraction mismatch for {key}\n"
                f"Returned:  {tgt.skipExtraction}\n"
                f"Expected:  {exp.get('sXtrct', False)}")
        
        if checkArchives:
            assert tgt.hasArchives == exp.get("hasArchives", True), (
                f"hasArchives mismatch for {key}\n"
                f"Returned:  {tgt.hasArchives}\n"
                f"Expected:  {exp.get('hasArchives', True)}")
            
        if checkInvalidFiles:
            expInvalid      = exp.get("invalidFiles", [])
            expInvalid      = expInvalid if isinstance(expInvalid, list) else [expInvalid]
            expInvalid      = {Path(f).resolve() for f in expInvalid}
            returnedInvalid = {f.resolve() for f in tgt.invalidFiles}
            assert returnedInvalid == expInvalid, (
                f"invalidFiles mismatch for {key}\n"
                f"Returned:  {returnedInvalid}\n"
                f"Expected:  {expInvalid}")

# Simulates a single archive being targeted
# chkTargets should return a tgtObj with the single arhive
def singleArchive():
    m.st("\n\n\nBegining Test singleArchive")
    if not os.path.isdir(testLocation):
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
# chkTargets should return a tgtObj with the archives
def multiArchive():
    m.st("\n\n\nBegining Test multiArchive")
    if not os.path.isdir(testLocation):
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
# chkTargets should return a tgtObj with the arhives found in the directory
def directoryWithSets():
    m.st("\n\n\nBegining Test directoryWithSets")
    if not os.path.isdir(testLocation):
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

# Simulates a directory with sets being targeted
# chkTargets should return a tgtObj with the arhives found in the directory
def directoryWithSymlinks():
    m.st("\n\n\nBegining Test directoryWithSymlinks")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_symlinks" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    { "path":       Path(testLocation, "directory_with_symlinks"),
      "archives": [ Path(testLocation, "directory_with_symlinks/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_symlinks/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_symlinks/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 },
    ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates a single archive being targeted with a long name
# chkTargets should return a tgtObj with the single arhive
def archiveWithLongName():
    m.st("\n\n\nBegining Test archiveWithLongName")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive\ -\ With\ Long\ NamepVtuq0\&+3TS9+.RghG\*Hid\*zvBC\%\;WdN_SKea7\*\#19J\;R%F\[\?%:\!bSg:TxD12345CzS0aZJ\%\%\%f%r7fe-e\;X\?36xEwj\%Z\!-\[z\;==bz\*0VAu5iVaAVaum\)b_\?vdW,AE\(\$8_39=wkdS\?-m+\;7cS5q5_G=\!vLZ\?xR\;Eg\%_vJUMj\(\?c-=CAeq00\[q\&X,25P\.zip" ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to check against
    { "path":       Path(testLocation),
      "archives": [ Path(testLocation, "Archive\ -\ With\ Long\ NamepVtuq0\&+3TS9+.RghG\*Hid\*zvBC\%\;WdN_SKea7\*\#19J\;R%F\[\?%:\!bSg:TxD12345CzS0aZJ\%\%\%f%r7fe-e\;X\?36xEwj\%Z\!-\[z\;==bz\*0VAu5iVaAVaum\)b_\?vdW,AE\(\$8_39=wkdS\?-m+\;7cS5q5_G=\!vLZ\?xR\;Eg\%_vJUMj\(\?c-=CAeq00\[q\&X,25P\.zip") ],
      "total": 1 
    }, ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates targeting multiple directories with archive sets
# chkTargets should return a tgtObj with the archives
def multiDirectoryWithSets():
    m.st("\n\n\nBegining Test multiDirectoryWithSets")
    if not os.path.isdir(testLocation):
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
# chkTargets should return a tgtObj with the archives
def multiDirectoryAndArchives():
    m.st("\n\n\nBegining Test multiDirectoryAndArchives")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                 f"{testLocation}directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip",
                 f"{testLocation}directory_with_directories_with_sets/directory1",
                 f"{testLocation}directory_with_directories_with_sets/directory2" ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 3
    assertTargets(tgtList, [
    # Results to test against
    { "path":       Path(testLocation, "directory_with_directories_with_sets"),
      "archives": [ Path(testLocation, "directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    },
    { "path":       Path(testLocation, "directory_with_directories_with_sets/directory1"),
      "archives": [ Path(testLocation, "directory_with_directories_with_sets/directory1/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with_sets/directory1/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with_sets/directory1/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    },{ "path":     Path(testLocation, "directory_with_directories_with_sets/directory2"),
      "archives": [ Path(testLocation, "directory_with_directories_with_sets/directory2/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with_sets/directory2/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with_sets/directory2/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    } ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates a directories being targted before multiple archives
# chkTargets should return a tgtObj with the archives
def multiDirectoryBeforeArchives():
    m.st("\n\n\nBegining Test multiDirectoryBeforeArchives")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_directories_with_sets/directory1",
                 f"{testLocation}directory_with_directories_with_sets/directory2",
                 f"{testLocation}directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                 f"{testLocation}directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip"  ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 3
    assertTargets(tgtList, [
    # Results to test against
    { "path":       Path(testLocation, "directory_with_directories_with_sets/directory1"),
      "archives": [ Path(testLocation, "directory_with_directories_with_sets/directory1/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with_sets/directory1/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with_sets/directory1/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    },
    { "path":     Path(testLocation, "directory_with_directories_with_sets/directory2"),
      "archives": [ Path(testLocation, "directory_with_directories_with_sets/directory2/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with_sets/directory2/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with_sets/directory2/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    },
    { "path":       Path(testLocation, "directory_with_directories_with_sets"),
      "archives": [ Path(testLocation, "directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_directories_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    } ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates a directory with no archives
# chkTargets should ignore everything and return an empty list
def directoryEmpty():
    m.st("\n\n\nBegining Test directoryEmpty")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_junk"),
      "archives":     [ ],
      "invalidFiles": [ ],
      "total": 0 }
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)

# Simulates a directory with sets being targeted that also has other misc files
# chkTargets should ignore the other files and return a tgtObj with the arhives found in the directory
def directoryWithJunkAndSets():
    m.st("\n\n\nBegining Test directoryWithJunkAndSets")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk_and_sets" ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to check against
    { "path":       Path(testLocation, "directory_with_junk_and_sets"),
      "archives": [ Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "total": 3 
    }, ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates skip extraction mode, working on an already extracted set
# chkTargets should return a tgtObj of all archives in the directory 
def directoryWithGames():
    m.st("\n\n\nBegining Test directoryWithGames")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_games" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":       Path(testLocation, "directory_with_games"),
      "archives": [ Path(testLocation, "directory_with_games/Another Fake Game (Vatican) (La).zip"),
                    Path(testLocation, "directory_with_games/Fake Game (Vatican) (La).zip"),
                    Path(testLocation, "directory_with_games/Yet Another Fake Game (Vatican) (La).zip") ],
      "total": 3, "sXtrct":   True } 
    ], checkTotal=True, checkSXtrct=True)
    m.st("Test completed Sucessfully")
    
# Simulates skip extraction mode, targeting parent of multiple already extracted sets
# chkTargets should return a tgtObj of all archives in the directory 
def multiDirectoryWithGames():
    m.st("\n\n\nBegining Test multiDirectoryWithGames")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_extracted_sets" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 3
    assertTargets(tgtList, [
    # Results to test against
    { "path":       Path(testLocation, "directory_with_extracted_sets"),
      "archives": [ ],
      "total": 0, "sXtrct":   True, "hasArchives": False  
    },
    { "path":       Path(testLocation, "directory_with_extracted_sets/directory_with_games"),
      "archives": [ Path(testLocation, "directory_with_extracted_sets/directory_with_games/Another Fake Game (Vatican) (La).zip"),
                    Path(testLocation, "directory_with_extracted_sets/directory_with_games/Fake Game (Vatican) (La).zip"),
                    Path(testLocation, "directory_with_extracted_sets/directory_with_games/Yet Another Fake Game (Vatican) (La).zip") ],
      "total": 3, "sXtrct":   True  
    },
    { "path":       Path(testLocation, "directory_with_extracted_sets/directory_with_games2"),
      "archives": [ Path(testLocation, "directory_with_extracted_sets/directory_with_games2/Another Fake Game (Vatican) (La).zip"),
                    Path(testLocation, "directory_with_extracted_sets/directory_with_games2/Fake Game (Vatican) (La).zip"),
                    Path(testLocation, "directory_with_extracted_sets/directory_with_games2/Yet Another Fake Game (Vatican) (La).zip") ],
      "total": 3, "sXtrct":   True } 
    ], checkTotal=True, checkSXtrct=True)
    m.st("Test completed Sucessfully")

# Simulates a directory with a bad zip file in skip extraction mode
# chkTargets should raise and extection and stop
def directoryWithBadGame():
    m.st("\n\n\nBegining Test directoryWithBadGame")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk_badfile_and_games" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_junk_badfile_and_games"),
      "archives":     [ Path(testLocation, "directory_with_junk_badfile_and_games/Another Fake Game (Vatican) (La).zip"),
                        Path(testLocation, "directory_with_junk_badfile_and_games/Fake Game (Vatican) (La).zip"),
                        Path(testLocation, "directory_with_junk_badfile_and_games/Yet Another Fake Game (Vatican) (La).zip") ],
      "invalidFiles": [ Path(testLocation, "directory_with_junk_badfile_and_games/Fake Game Thats Not Actually an Archive.zip") ],
      "total": 3, "sXtrct":   True },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates a single archive being targeted that has bad permissions
# chkTargets should raise a PermissionError
def directoryWithBadGamesPermissions():
    m.st("\n\n\nBegining Test directoryWithBadGamesPermissions")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "directory_with_games/Fake Game (Vatican) (La).zip", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_games" ]
    # Compile list in output format to check against
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    os.chmod(testLocation + "directory_with_games/Fake Game (Vatican) (La).zip", 0o777)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_games"),
      "archives":     [ Path(testLocation, "directory_with_games/Another Fake Game (Vatican) (La).zip"),
                        Path(testLocation, "directory_with_games/Yet Another Fake Game (Vatican) (La).zip") ],
      "invalidFiles": [ Path(testLocation, "directory_with_games/Fake Game (Vatican) (La).zip") ],
      "total": 2, "sXtrct":   True },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates a directory being targeted that has bad permissions
# chkTargets should raise a PermissionError
def directoryWithBadPermsSXstrct():
    m.st("\n\n\nBegining Test directoryWithBadPermsSXstrct")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "directory_with_junk", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Compile list in output format to check against
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    os.chmod(testLocation + "directory_with_junk", 0o777)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_junk"),
      "archives":     [ ],
      "invalidFiles": [ ],
      "total": 0, "sXtrct":   True },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")
    
# Simulates a directory with no roms in skip extraction mode
# chkTargets should ignore everything and return an empty list
def directoryEmptyXStrct():
    m.st("\n\n\nBegining Test directoryEmptyXStrct")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_junk"),
      "archives":     [ ],
      "invalidFiles": [ ],
      "total": 0, "sXtrct":   True }
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)

# Simulates a single archive being targeted that has bad permissions
# chkTargets should raise a PermissionError
def archiveWithBadPermissions():
    m.st("\n\n\nBegining Test archiveWithBadPermissions")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With Bad Permissions.zip" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o777)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation),
      "archives":     [ ],
      "invalidFiles": [ f"{testLocation}Archive - With Bad Permissions.zip" ],
      "total": 0 },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates a single archive being targeted that has a passwordthat has bad permissions
# chkTargets should return no tgtObjs
def archiveWithAPasswprd():
    m.st("\n\n\nBegining Test archiveWithAPasswprd")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With A Password.zip" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 0
    assertTargets(tgtList, [ ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates a single archive being targeted that has bad permissions
# chkTargets should raise a PermissionError
def directoryWithBadPermissions():
    m.st("\n\n\nBegining Test directoryWithBadPermissions")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "directory_with_junk", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    os.chmod(testLocation + "directory_with_junk", 0o777)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_junk"),
      "archives":     [ ],
      "invalidFiles": [ ],
      "total": 0 },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates a single invalid archive being targeted
# chkTargets should raise a ValueError
def archiveWithSmallSize():
    m.st("\n\n\nBegining Test archiveWithSmallSize")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With Minimal Filesize.zip" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation),
      "archives":     [ ],
      "invalidFiles": [ Path(testLocation, "Archive - With Minimal Filesize.zip") ],
      "total": 0 },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates a invalid archive mixed in with good archives
# chkTargets return a tgtObj excluding the bad file
def oneBadArchive():
    m.st("\n\n\nBegining Test oneBadArchive")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip",
                f"{testLocation}Archive - Thats Not Actually an Archive.zip" ]  
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 2
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_sets"),
      "archives":     [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                        Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                        Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "invalidFiles": [ ],
      "total": 3 },
    { "path":           Path(testLocation),
      "archives":     [ ],
      "invalidFiles": [ Path(testLocation, "Archive - Thats Not Actually an Archive.zip") ],
      "total": 0 },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates targeting an archive with unicode charcters
# chkTargets should return a tgtObj with the single arhive
def archiveWithUnicode():
    m.st("\n\n\nBegining Test archiveWithUnicode")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With Unicodeⱒ⨤⫔⧮✑⹼⭸⩛⠴␼⨤ℷ♱↬≭Ⳁ⸌⤙ⅴ⊁⯚.zip" ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to check against
    { "path":       Path(testLocation),
    "archives": [ Path(testLocation, "Archive - With Unicodeⱒ⨤⫔⧮✑⹼⭸⩛⠴␼⨤ℷ♱↬≭Ⳁ⸌⤙ⅴ⊁⯚.zip") ],
    "total": 1 
    }, ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates targeting the same archive twice
# chkTargets should return a tgtObj with the single arhive
def archiveSameTwice():
    m.st("\n\n\nBegining Test archiveSameTwice")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}Archive - With 3 Top Level Games (Normal Set).zip" ]
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

# Simulates a invalid archive mixed in with good archives
# chkTargets return a tgtObj excluding the bad file
def oneBadArchivePermissions():
    m.st("\n\n\nBegining Test oneBadArchivePermissions")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip",
                f"{testLocation}Archive - With Bad Permissions.zip" ]    
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o777)
    dumpTargets(tgtList)
    assert len(tgtList) == 2
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_sets"),
      "archives":     [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"),
                        Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"),
                        Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip") ],
      "invalidFiles": [ ],
      "total": 3 },
    { "path":           Path(testLocation),
      "archives":     [ ],
      "invalidFiles": [ Path(testLocation, "Archive - With Bad Permissions.zip") ],
      "total": 0 },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates an empty target list
# chkTargets should return no tgtObjs
def noTarget():
    m.st("\n\n\nBegining Test noTarget")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 0
    assertTargets(tgtList, [ ], checkTotal=True)
    m.st("Test completed Sucessfully")

# Simulates a single non-archive file being target
# chkTargets should return a single tgtObj with file in invalid list
def badTarget():
    m.st("\n\n\nBegining Test badTarget")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk/junk.txt" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 1
    assertTargets(tgtList, [
    # Results to test against
    { "path":           Path(testLocation, "directory_with_junk"),
      "archives":     [ ],
      "invalidFiles": [ Path(testLocation, "directory_with_junk/junk.txt") ],
      "total": 0 },
    ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# Simulates a single system file being targeted
# chkTargets should return a single tgtObj with file in invalid list
def badTargetSys():
    m.st("\n\n\nBegining Test badTarget")
    if not os.path.isdir(testLocation):
        setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ "/dev/null" ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    dumpTargets(tgtList)
    assert len(tgtList) == 0
    assertTargets(tgtList, [ ], checkTotal=True, checkSXtrct=True, checkInvalidFiles=True)
    m.st("Test completed Sucessfully")

# TODO nested directories in skip extract
# TODO currupted archive case
# TODO parent with set in sub but also junk in sub
tests()