import sys
import os
#import pytest
from pathlib import Path
from rom import romFile
from messenger import messenger
from all_known_games import ALL_GAMES

#for fileName, expected in DEBUG_CASES:
for fileName in ALL_GAMES:
    ra_zipPath = "/home/john/.local/tmp"
    ra_extPath = Path("tmp", "testcases")
    ra_m = messenger(debug=False, verbose=False)
    results = [ ]
    rom_name = str(fileName + ".zip")

    #print(f"testing: {rom_name}")
    #print(f"expected: {expected}")
    #print(f"romFile({rom_name}, {ra_zipPath}, {ra_extPath}, ra_m)")
    #romObj = romFile(rom.name, ra.zipPath, ra.extPath, ra.m)
    romObj = romFile(rom_name, ra_zipPath, ra_extPath, ra_m)
    rom_tags = romObj.scrape()
    rom_sort = romObj.sort()
    #print(f"scrape returned: {rom_tags}")
    #print(f"sort returned: {rom_sort}")
    #results.append((rom_name, rom_sort))
    #print(f"result is {results}")
    #with open("allNamesOutput.txt", "a") as file:
    #    for fn, srtloc in results:
    #        file.write(f"{fn}, {srtloc}\n")


    #assert rom_sort == expected, (
    #    f"sort() returned {rom_sort} for {rom_name} (expected: {expected})\n"
    #    f"  tags: rom_tags" )