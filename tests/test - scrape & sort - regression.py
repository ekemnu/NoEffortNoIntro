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
    
    parser.add_argument('-d', '--debug', action=argparse.BooleanOptionalAction, dest='debug',
                        default=False, help='Runs the RERESSION_DEBUG cases from testcases.py')
    flags = parser.parse_args()
    return flags

flags = argParser()

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