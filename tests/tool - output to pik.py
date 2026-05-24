import sys
import os
import ast
from pathlib import Path
from rom import romFile
from messenger import messenger

# Initialize variables to match what romFile expects
ra_zipPath = "/home/john/.local/tmp"
ra_extPath = Path("tmp", "testcases")

import pickle
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

with open("pickledump.pkl", "wb") as f:
    pickle.dump(results, f)