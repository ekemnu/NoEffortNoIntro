import sys
import os
import argparse
#import pytest
from pathlib import Path
from rom import romFile
from messenger import messenger
from testcases import SORT_CASES, SCRAPE_CASES, DEBUG_CASES

def argParser():
    parser = argparse.ArgumentParser( description='Tests NeNI scrape and sort logic',
                        epilog='Written by John Loreth 2026')
    parser.add_argument('-s', '--sort', action=argparse.BooleanOptionalAction, dest='sort',
                        help='Runs the SORT_CASES from testcases.py')
    parser.add_argument('-k', '--scrape', action=argparse.BooleanOptionalAction, dest='scrape',
                        help='Runs the SCRAPE_CASES from testcases.py')
    parser.add_argument('-d', '--debug', action=argparse.BooleanOptionalAction, dest='debug',
                        help='Runs the DEBUG_CASES from testcases.py')
    flags = parser.parse_args()
    return flags

flags = argParser()

if flags.sort:
    CASES = SORT_CASES
if flags.scrape:
    CASES = SCRAPE_CASES
if flags.debug:
    CASES = DEBUG_CASES

#for fileName, expected in DEBUG_CASES:
for fileName, expected in CASES:
    ra_zipPath = "/home/john/.local/tmp"
    ra_extPath = Path("tmp", "testcases")
    rom_name = str(fileName + ".zip")

    ra_m = messenger(debug=True, verbose=True)
    print(f"testing: {rom_name}")
    print(f"expected: {expected}")
    print(f"romFile({rom_name}, {ra_zipPath}, {ra_extPath}, ra_m)")
    romObj = romFile(rom_name, ra_zipPath, ra_extPath, ra_m)
    rom_tags = romObj.scrape()
    rom_sort = romObj.sort()
    print(f"scrape returned: {rom_tags}")
    print(f"sort returned: {rom_sort}, expected: {expected}")
    assert rom_sort == expected, (
        f"sort() returned {rom_sort} for {rom_name} (expected: {expected})\n"
        f"  tags: rom_tags" )