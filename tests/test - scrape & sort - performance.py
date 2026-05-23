from pathlib import Path
from rom import romFile
from messenger import messenger
from all_known_games import ALL_GAMES

# Initialize variables to match what romFile expects
ra_zipPath = Path("home", "john", ".local", "tmp")
ra_extPath = Path("tmp", "testcases")
ra_m = messenger(debug=False, verbose=False)

### Low overhead code path for performance profiling ###
for fileName in ALL_GAMES:
    rom_name = str(fileName + ".zip")

    # Feed mock file data into romFile
    romObj = romFile(rom_name, ra_zipPath, ra_extPath, ra_m)
    # Trigger romFile to scrape all tags from file name
    rom_tags = romObj.scrape()
    # Trigger romFile to sort the filename
    rom_sort = romObj.sort()
exit(0)