import sys
import os
import ast
import argparse
import pickle
from pathlib import Path
from rom import romFile
from messenger import messenger

def argParser():
    parser = argparse.ArgumentParser( description='Tests NeNI scrape and sort logic',
                        epilog='Written by John Loreth 2026')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', '--performance', action=argparse.BooleanOptionalAction, dest='perfm',
                        help='Tests scrape() and sort() against all_known_games.py with as little overhead as possible')
    group.add_argument('-o', '--output', action='store', nargs='?',
                        default=False, dest='outPut',
                        help='When regression testing, specifies if and where a output file should be created (default: ~/.local/tmp)')
    parser.add_argument('-d', '--debug', action=argparse.BooleanOptionalAction, dest='debug',
                        default=False, help='Runs the RERESSION_DEBUG cases from testcases.py')
    flags = parser.parse_args()
    return flags

flags = argParser()

# Initialize variables to match what romFile expects
ra_zipPath = "/home/john/.local/tmp"
ra_extPath = Path("tmp", "testcases")
valFile = "allGamesOutput-Regression.pkl"

### Low overhead code path for performance profiling ###
if flags.perfm:
    # Sets debug and verbose to off to save message writing time
    ra_m = messenger(debug=False, verbose=False)
    with open("tests/validation-performance-all games list.pkl", "rb") as c:
        CASES = pickle.load(c)

    for fileName in CASES:
        rom_name = str(fileName + ".zip")

        # Feed mock file data into romFile
        romObj = romFile(rom_name, ra_zipPath, ra_extPath, ra_m)
        # Trigger romFile to scrape all tags from file name
        rom_tags = romObj.scrape()
        # Trigger romFile to sort the filename
        rom_sort = romObj.sort()
    exit(0)

if flags.outPut:
    from all_known_games import ALL_GAMES
    ra_m = messenger(debug=False, verbose=False)

    results = [ ]
    
    for fileName in ALL_GAMES:
        rom_name = str(fileName + ".zip")

        # Feed mock file data into romFile
        romObj = romFile(rom_name, ra_zipPath, ra_extPath, ra_m)
        # Trigger romFile to scrape all tags from file name
        rom_tags = romObj.scrape()
        # Trigger romFile to sort the filename
        rom_sorted = romObj.sort()   
        
        results.append((fileName, rom_sorted, rom_tags))
    
    if flags.pik:
        with open("allGamesOutput-Regression.pkl", "wb") as f:
            pickle.dump(results, f)
    else:
        with open("allNamesOutput.txt", "a") as file:
            for fn, srtloc, tags in results:
                file.write(f"( \"{fn}\", \"{srtloc}\", \"{tags!r}\" ),\n")
    exit(0)

### Test for regressions code path ###
ra_m = messenger(debug=False, verbose=False)
with open(valFile, "rb") as c:
    CASES = pickle.load(c)

for fileName, expectedSrt, expectedTags in CASES:
    rom_name = str(fileName + ".zip")
    #expectedTags = ast.literal_eval(expectedTags)
    
    # Feed mock file data into romFile
    romObj = romFile(rom_name, ra_zipPath, ra_extPath, ra_m)
    # Trigger romFile to scrape all tags from file name
    rom_tags = romObj.scrape()
    # Trigger romFile to sort the filename
    rom_sorted = romObj.sort()   
    
    if not flags.outPut:
        assert rom_tags == expectedTags, (
            f"\nFileName: {rom_name}\n" 
            f"Returned: {rom_tags}\n"
            f"Expected: {expectedTags}\n"
            f"Sorted:   {rom_sorted}\n"
            f"Tag Error" )
        
        assert rom_sorted == expectedSrt, (
            f"\nFileName: {rom_name}\n" 
            f"Returned: {rom_tags}\n"
            f"Expected: {expectedSrt}\n"
            f"Sorted:   {rom_sorted}\n" 
            f"Sort Error" )