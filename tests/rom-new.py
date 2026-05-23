from dataclasses import dataclass, field
from typing import ClassVar
import re                       # Used to perform regex searches
import sys                      # Used to exit the script
from itertools import chain     # Used to combine dictionary values into a list
from pathlib import Path


##### Skeleton object for each rom in the target archive
@dataclass
class romFile:
    romRegion: ClassVar[dict] = {
            "USA": ( "USA", "Canada" ),
            "Japan": ( "Japan",),
            "Europe": ( "Europe", "Australia", "United Kingdom", "New Zealand", "PAL" ),
            "EurWor": ( "Germany", "France", "Spain", "Italy", "Netherlands", "Sweden", "Denmark", "Norway", "Finland", "Poland", "Greece", "Portugal", "Hungary", "Austria", "Scandinavia" ),
            "World":  ( "World", "Asia", "Taiwan", "Korea", "China", "Brazil", "Russia", "Hong Kong", "Peru", "Argentina", "Mexico", "India", "Latin America" )
    }
    romLang: ClassVar[tuple] = ( 
            "En", "Fr", "Es", "De", "It", "Nl", "Ja", "Da", "Sv", "Pt", "No", "Fi", "Ru", "Ko", "Zh", "Pl", "Tr", "Cs", "Ar", "Zh-Hant", "Zh-Hans", 
            "El", "Fr-CA", "Hr", "Hu", "Pt-BR", "Ca", "En-US", "En-GB", "Es-XL", "Yi", "Gd", "Sl", "Kw", "Ro", "Es-MX", "Pt-PT", "Es-ES"
    )
    romRegions: ClassVar[list] = list(chain(*romRegion.values()))       # Get a list of all regions in the romRegion dictionary
    
    m: object                                                 # Messener for writing lines to the terminal
    name: str                                                 # File name of the file
    parent: Path                                              # Parent archive the file was extracted from
    location: Path                                            # Stores in what directory the file is located
    path: Path = field(init=False)                            # Stores full path to file
    srtLocation: str = field(default="",  init=False)         # Directory relative to root ext dir to which the file should be moved
    outLocation = str = field(default="",  init=False)        # Final location of sorted rom
    region = list = field(default_factory=list, init=False)   # Region(s) as scraped from file's tags
    language = list = field(default_factory=list, init=False) # Language(s) as scraped from the file's tags
    infoTags = list = field(default_factory=list, init=False) # Misc tag(s) scraped from the file's tags
    srtRegion = str = field(default="",  init=False)          # Stores sort region determined by the sort method
    srtLanguage = str = field(default="",  init=False)        # Stores sort language determined by the sort method
    tags  = dict = field(default_factory=dict, init=False)    # Stores a list of all the tags from the scrape method

    def __post_init__(rf):
        rf.path = rf.location / rf.name                       # Creates fully qualified path to file
    
    # Takes the full file name of the current working file, scrapes it for tags and returns those tags
    def scrape(rf):
        rf.m.sb("Gathering tags...")
        rawTags = re.findall(r'\((?=[^(]*\))(.*?)\)', rf.name)          # Scrape file name for all occurrences of (***)

        if rawTags:                                                     # If the file has tags
            for tag in rawTags:                                         # For each of the collected tags
                for splitTag in re.split(r'[,+]', tag):                 # For each individual tag split on , and +
                    splitTag = splitTag.strip()                         # Strip whitespace
                    # Classify each tag
                    if splitTag in rf.romRegions:                       # If the tag can be found in the regions list
                        rf.region.append(splitTag)                      # Add it to the regionTags list
                    elif splitTag in rf.romLang:                        # If the tag matches the format of a language tag
                        rf.language.append(splitTag)                    # Add it to the languageTags list
                    elif splitTag.startswith("PAL"):                    # If the Tag is a PAL variant
                        rf.region.append("PAL")                         # Add it to the regionTags list
                    else:
                        rf.infoTags.append(splitTag)                    # Add it to the miscTags list
        
        rf.tags = { "unSrted": rawTags, 
                    "regionTags": rf.region, 
                    "languageTags": rf.language,
                    "miscTags": rf.infoTags }
        
        rf.m.sb("Tags are:", ' '.join(rf.tags["unSrted"])) 
        return rf.tags

    # Takes a given romFile and its scraped tags and sorts it into one of the sort regions
    # Returns either the sort region or 1 for unmatched.
    # TODO: Properly handle home region and language priorities
    def sort(rf):
        regionTags = rf.tags["regionTags"]
        languageTags = rf.tags["languageTags"]
        regionUSA = rf.romRegion["USA"]
        regionEurope = rf.romRegion["Europe"]
        regionEurWor = rf.romRegion["EurWor"]
        regionWorld  = rf.romRegion["World"]
        regionJapan  = rf.romRegion["Japan"]

        rf.m.sb("Sorting rom...")
        # Try to match on language if no region tags
        if not regionTags:
            if not languageTags:                    # If there are not language tags return unknown
                return "UnKwn"
            if "En" in languageTags:                # If there is an english language tag return USA
                return "USA"
            elif "Ja" in languageTags:              # If there is a japanese language tag return Japan
                return "Japan"
            return "World"                          # If it has any other language tag return World
        
        # Attempt to bail out early by matching on master sort regions
        if "USA" in regionTags:
            return "USA"
        
        if "Europe" in regionTags or "PAL" in regionTags:
            if not languageTags or "En" in languageTags:
                return "Europe"
            
        if "Japan" in regionTags:
            otherRegions = [r for r in regionTags if r != "Japan"]
            if not otherRegions:
                return "Japan"
            if any(r in regionEurope for r in otherRegions):
                if not languageTags or "En" in languageTags:
                    return "Europe"
            if any(r in regionUSA for r in otherRegions):
                if not languageTags or "En" in languageTags:
                    return "USA"
            if "World" in otherRegions:
                if not languageTags or "En" in languageTags:
                    return "USA"
            return "Japan"
    
        if "World" in regionTags:
            if "En" in languageTags:
                return "USA"
            if "Ja" in languageTags:
                return "Japan"
            if languageTags and "En" not in languageTags:
                return "World"
            return "USA"
        
        # If we weren't able to bail out, match region against master list
        for tag in regionTags:
            if tag in rf.romRegion["USA"]:
                if not languageTags or "En" in languageTags:
                    return "USA"
                return "World"
            if tag in regionEurope:
                if not languageTags or "En" in languageTags:
                    return "Europe"
                else:
                    return "World"
            if tag in regionWorld:
                return "World"
            if tag in regionEurWor:
                if not "En" in languageTags:
                    return "World"
                return "Europe"
            if tag in regionJapan:
                return "Japan"
        
        # Catch anything else that fell through the cracks
        return "UnKwn"
    
    ##### Move the rom to the sorted location
    def move(rf):
        # Attempt to move the rom to the sorted location
        try:
            rf.path.rename(rf.srtLocation.joinpath(rf.name))
        # Error if unable to move
        except Exception as e:
            rf.m.er("Unable to move", rf.name, "to sort location", rf.srtLocation, str(e))
            rf.m.ex("Error")
            sys.exit(1)
        else:
            # Notify user of successful move
            rf.m.mv(rf.name, rf.srtRegion)
            return 0