import os
import sys
import shutil
from pathlib import Path
import zipfile
from neni import chkTargets as check_targets
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
def tests():
    #singleArchive()                    # Tests normal logic path
    #multiArchive()                     # Tests more than one set targeted
    #directoryWithSets()                # Tests multi-target logic path
    #multiDirectoryWithSets()           # Tests multiple targets containing sets
    #multiDirectoryAndArchives()        # Tests multiple targets and multiple directories called at same time
    #multiDirectoryBeforeArchives()     # Tests multiple directories and multiple archives being called
    #directoryEmpty()                   # Tests if called on directory with no archives
    #directoryWithJunkAndSets()         # Tests if irrelevant files are being ignored
    #directoryWithGames()               # Tests skip extraction mode
    multiDirectoryWithGames()           # Tests targeting parent of multiple extracted sets
    #directoryWithBadGame()             # Tests skip extract if there is a bad file
    #directoryWithBadGamesPermissions() # Tests a permissions error with a file in skip extract mode
    #directoryWithBadPermsSXstrct()     # Tests a directory with bad permissions in skip extract mode
    #directoryEmptyXStrct()             # Tests if called on an empty directory in skip extract mode                 
    #archiveWithBadPermissions()        # Tests hanlding of archives neni can't access
    #directoryWithBadPermissions()      # Tests handling a target direcory with bad permissions
    #archiveWithSmallSize()             # Tests if one bad archive spoils the bunch
    #oneBadArchive()                    # Tests handling of a bad archive mixed in with good
    #oneBadArchivePermissions()         # Tests a multiarchive target, one of which has bad perms

def chkTargets(targets, sXtrct, msg):    
    m = msg
    tgtList = []
    
    class _isDir(Exception):
        pass
    class TargetNotFound(Exception):
        pass
    
    def _targetCheck(target):
        if target.is_file():
            # Check that we have permission to access the target
            if not os.access(target, os.R_OK):
                raise PermissionError (f"No Permissions for target: {target.resolve()}")
            # Check that the archive has a filesize more than minimum
            if target.stat().st_size <= 22:
                raise ValueError (f"Not a valid file: {target.resolve()}, Filesize: {target.stat().st_size}B") 
            # Check that the target is a valid zipfile
            if target.suffix.lower() == ".zip": 
                if zipfile.is_zipfile(target):
                    # Check to see if file 
                    # Target was a file, add it to the target list
                    return target.resolve()
                else:
                    raise ValueError (f"Not a valid zipfile: {target.resolve()}")
            raise ValueError (f"Not a valid zipfile: {target.resolve()}")
        
        # If the target wasn't a file, was it a directory?
        elif target.is_dir():
            # Check that we have permission to access the target
            if not os.access(target, os.R_OK):
                raise PermissionError (f"No Permissions for target: {target.resolve()}")
            
            # Target will be a directory of individual rom files
            if sXtrct:
                tgtList = [ ]
                for target in targets:
                    target = Path(target)
                    
                    # Ensure we have permission to read the directory
                    if not os.access(target, os.R_OK):
                        raise PermissionError (f"No Permissions for target: {target.resolve()}")
                    
                    # Only directories can be targeted in skip extract mode
                    if not target.is_dir():
                        raise ValueError ("Target wasn't a directory")
                    
                    # Gather all zip files in the directory
                    _romList = list(target.glob('*.zip', case_sensitive=None))

                    # Error if the directory was empty
                    if not _romList:
                        raise TargetNotFound ("Directory is empty")

                    # Test that all archives in the target are valid
                    for _romf in _romList:
                        if not zipfile.is_zipfile(_romf):
                            raise ValueError (f"Bad file found: {_romf}")
            
            raise _isDir ("Target is a directory")
        
        # Check to see if target exsists and is valid file and extension is .zip
        else:
            raise ValueError (f"Not a valid file: {target.resolve()}")

    m.st("Checking target(s)...")
    # Dedupe the list before running
    
    targets = targets.copy()
    while targets:
        for target in targets:
            tgtIndex = targets.index(target)
            target   = Path(target)
            try:
                tgtList.append(_targetCheck(target))            
            except PermissionError as e:
                m.er("Permission Error: Cannot Access", str(target.resolve()))
                m.ei("Please verify you have permissions to access this file")
            except ValueError as e:
                m.er(str(e))
                m.ei("Please verify this is a valid archive file")                
            except _isDir as e:
                _zipList = []
                m.st("Gathering Archives From Target Directory...", str(target.resolve()))
                for _dir in target.iterdir():
                    _zipList.extend([ f.resolve() for f in target.glob('*.zip', case_sensitive=None) ])
                    targets.extend(_zipList)
                    # Target is a directory, scan it for archives
                    for tgtFile in _zipList:
                        m.st("Discovered", tgtFile.name, "in Target Directory")
            del targets[tgtIndex]

    if not tgtList:
        # Error if no archives could be found
        m.er("Unable To Find Valid Target(s)")
        m.ei("Please supply a valid path to either a single archive, or a directory with No-Intro archives and run NeNi again")
        m.ei("  Ex: $ neni /home/user/Downloads/archive.zip")
        m.ei("  or: $ neni /home/user/Downloads/NoIntroArchives")
        m.ex("Error")
        raise TargetNotFound (f"target not found")
    
    # Return the list of full paths to the targets
    return tgtList

# Simulates a single archive being targeted
# chkTargets should return a list with the single arhive
def singleArchive():
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}Archive - With 3 Top Level Games (Normal Set).zip" ]
    # Compile list in output format to check against
    expected = [ Path(testLocation, "Archive - With 3 Top Level Games (Normal Set).zip").resolve() ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    
# Simulates a multiple archives being targeted
# chkTargets should return a list with the archives
def multiArchive():
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                 f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip" ]
    # Compile list in output format to check against
    expected  = [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve() ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )

# Simulates a directory with sets being targeted
# chkTargets should return a list with the arhives found in the directory
def directoryWithSets():
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets" ]
    # Compile list in output format to check against
    fileOne      = Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve()
    fileTwo      = Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve()
    fileThree    = Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve()
    expected     = [ fileTwo, fileThree, fileOne ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    
def multiDirectoryWithSets():
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets",
                 f"{testLocation}directory_with_junk_and_sets" ]
    # Compile list in output format to check against
    expected = [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve(),
                 Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve(),
                 Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve(),
                 Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve(),
                 Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve(),
                 Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve() ]
    
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )

# Simulates a multiple archives and directories being targeted
# chkTargets should return a list with the archives
def multiDirectoryAndArchives():
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                 f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip", 
                 f"{testLocation}directory_with_sets",
                 f"{testLocation}directory_with_junk_and_sets"]
    # Compile list in output format to check against
    expected  = [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"), 
    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip"), 
    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"), 
    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip"), 
    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)3.zip"), 
    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip"), 
    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip"), 
    Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set).zip"), 
    Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip") ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )



# Simulates a directories being targted before multiple archives
# chkTargets should return a list with the archives
def multiDirectoryBeforeArchives():
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets",
                 f"{testLocation}directory_with_junk_and_sets",
                 f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                 f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                 f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip", ]
                 
    # Compile list in output format to check against
    expected  = [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve(),
                  Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve(),
                  Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve(),
                  Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve() ]
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )

# Simulates a directory with no archives
# chkTargets should ignore everything and return an empty list
def directoryEmpty():
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk" ]
    # Compile list in output format to check against
    expected     = [ ]
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
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_junk_and_sets" ]
    # Compile list in output format to check against
    fileOne      = Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve()
    fileTwo      = Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve()
    fileThree    = Path(testLocation, "directory_with_junk_and_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve()
    expected     = [ fileTwo, fileThree, fileOne ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )

# Simulates skip extraction mode, working on an already extracted set
# chkTargets should return a list of all archives in the directory 
def directoryWithGames():
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_games" ]
    # Compile list in output format to check against
    expected = [ Path(testLocation, "directory_with_games/Fake Game (Vatican) (La).zip").resolve(), 
                 Path(testLocation, "directory_with_games/Yet Another Fake Game (Vatican) (La).zip").resolve(), 
                 Path(testLocation, "directory_with_games/Another Fake Game (Vatican) (La).zip").resolve() ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    
# Simulates skip extraction mode, targeting parent of multiple already extracted sets
# chkTargets should return a list of all archives in the directory 
def multiDirectoryWithGames():
    setupEnv()
    # Mock dir(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_extracted_sets/directory_with_games",
                 f"{testLocation}directory_with_extracted_sets/directory_with_games2" ]
    # Compile list in output format to check against
    expected = [ Path(testLocation, "directory_with_games/Fake Game (Vatican) (La).zip").resolve(), 
                 Path(testLocation, "directory_with_games/Yet Another Fake Game (Vatican) (La).zip").resolve(), 
                 Path(testLocation, "directory_with_games/Another Fake Game (Vatican) (La).zip").resolve(),
                 Path(testLocation, "directory_with_games2/Fake Game (Vatican) (La).zip").resolve(), 
                 Path(testLocation, "directory_with_games2/Yet Another Fake Game (Vatican) (La).zip").resolve(), 
                 Path(testLocation, "directory_with_games2/Another Fake Game (Vatican) (La).zip").resolve() ]
    # Call chkTargets to run the test
    tgtList = chkTargets(targets, True, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )

# Simulates a directory with a bad zip file in skip extraction mode
# chkTargets should raise and extection and stop
def directoryWithBadGame():
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
    setupEnv()
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip",
                f"{testLocation}Archive - Thats Not Actually an Archive.zip" ]
    # Compile list in output format to check against
    expected  = [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve() ]    
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    
# Simulates a invalid archive mixed in with good archives
# chkTargets return a list excluding the bad file
def oneBadArchivePermissions():
    setupEnv()
    # Set unreadable permissions to prepare the test case
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o000)
    # Mock file(s) to be passed to chkTargets
    targets  = [ f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip",
                f"{testLocation}directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip",
                f"{testLocation}Archive - With Bad Permissions.zip" ]
    # Compile list in output format to check against
    expected  = [ Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set).zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)3.zip").resolve(),
                  Path(testLocation, "directory_with_sets/Archive - With 3 Top Level Games (Normal Set)2.zip").resolve() ]    
    # Call chkTargets to run the test
    tgtList  = chkTargets(targets, False, m)
    print(f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )
    os.chmod(testLocation + "Archive - With Bad Permissions.zip", 0o777)
    assert tgtList == expected, ( 
        f"\nReturned: {tgtList}\n"
        f"Expected: {expected}\n" )

# TODO targeted a non-zip
# TODO nested directories in skip extract
tests()
