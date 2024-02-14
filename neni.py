#####   No Intro Roms Handler
#####	John Loreth
#####	2024
#####	v0.2
#####
#####   Process and extracts No-Intro Rom Archives, sorts by region into sub directories
#####
#####   Version history:
#####		0.1  Basic bash script
#####       0.2  Rewritten in Python
#####       0.3  
#####       0.4  

import re
import os
#import os.path
#import shutil
import subprocess
import sys
from itertools import chain
    
# Gets the arguments passed to the script from bash
print("DEBUG: sys.argv is", sys.argv, "type is", type(sys.argv))
scriptFn = sys.argv[0]
try:
    sys.argv[1]                                 # Checks to see if script was called without arguments
except Exception:                               # If the script was run without arguments
    print("Error: Must specify a file")
    print("       Run the script again supplying a valid path to a No-Intro rom archive")
    print("         Ex: $", scriptFn, "/home/user/Downloads/archive.zip")
    quit(1)
else:                                           # If the script was run with arguments
    print("DEBUG: sys.argv[1:] is ", sys.argv[1:], "type is ", type(sys.argv[1:]))
    zipFile = os.path.abspath(' '.join(sys.argv[1:]))
    print("DEBUG: zipFile is", zipFile, type(zipFile))

# Checks if target file is a zip file
def checkZip():
    global zipPath
    global zipFn
    global zipFnRoot
    global zipFnExt
    
    try:
        os.path.isfile(zipFile)             # Checks if target file exsists
    except Exception:                           # Error if the file does not exsist
        print("Error: Target File Cannot Be Found")
        print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
        print("         Ex: $", scriptFn, "/home/user/Downloads/archive.zip")
        quit(1)
    else:                                       # If the file exsists
        zipPath, zipFn = os.path.split(zipFile)
        zipFnRoot, zipFnExt = os.path.splitext(zipFn)
        #zipPath = zipPath.replace(" ", "\\ ")
        #zipFnRoot = zipFnRoot.replace(" ", "\\ ")
        print("DEBUG: zipPath is:", zipPath, type(zipPath), "zipFn is:", zipFn, type(zipFn), "zipFnRoot is:", zipFnRoot, type(zipFnRoot), "zipFnExt is:", zipFnExt, type(zipFnExt))
        if ".zip" not in zipFnExt:
            print("Error: Target File is no a Zip Archive")
            print("       Check that you've supplied a valid path to a No-Intro zip archive and run the script again")
            print("         Ex: $", scriptFn, "/home/user/Downloads/archive.zip")
            quit(1)
        else:
            print("DEBUG: entered else")
    		
def unzip():
        global extPath
        
        # STILL NEED TO CHECK IF EXT PATH IS THERE
        
        print("DEBUG: entered unzip")
        extPath = os.path.join(zipPath, zipFnRoot)
        bashCMD = 'echo -d', extPath.replace(" ", "\ "), zipFile.replace(" ", "\ ")
        print("DEBUG: extPath is", extPath, type(extPath))
        execBash(' '.join(bashCMD))
        if bash.returncode == 0:
            print(scriptFn, ": Sucessfully decompressed archive to", extPath)
        else:
            print("Error: Archive Decompression Failed\n", bash.stderr)
            quit(1)
            
def processRom():
    global romRegion
    global romLang
    global rom
    global eurPath
    global jpnPath
    global worPath
    global regions
    
    romRegion = {
            "USA": ( "USA", "Canada" ),
            "Japan": ( "Japan", "null" ),
            "Europe": ( "Europe", "Australia", "PAL" ),
            "World": ( "World", "Asia", "Brazil", "China", "France", "Germany", "Hong Kong", "Italy", "Korea", "Netherlands", "Spain", "Sweden", "Scandinavia", 'Latin America', 'Taiwan' )
    }
    romLang = ( "En", "Jp", "Fr", "De", "Es", "It", "Nl", "Pt", "Sv", "No", "Da", "Fi", "Zh", "Ko", "Pl", "Ca", "Kw", "El", "Pt-BR", "Pt-PT", "ES-XL", "Ru" )
    regions = list(chain(*romRegion.values()))
    
   # def gatherTags(rom):
   #     tagList = []
   #     tagsCollected = re.findall(r'\((.*?)\)', rom)
   #     for tag in tagsCollected:
   #         tagSplit = tag.split(',')
   #         tagList.extend(tagSplit)
   #     return tagList
        
    def gatherTags(rom):
        regionTags = []
        languageTags = []
        miscTags = []
        
        tagsCollected = re.findall(r'\((.*?)\)', rom)
        for tag in tagsCollected:
            tagSplit = tag.split(', ')
            for splitTag in tagSplit:
                print("DEBUG: splitTag is:", splitTag, type(splitTag)) 
                if splitTag in regions:
                    regionTags.append(splitTag)
                elif splitTag in romLang:
                    languageTags.append(splitTag)
                else:
                    miscTags.append(splitTag)
        print("DEBUG: regionTags is:", regionTags, type(regionTags)) 
        tags = { "regionTags" : regionTags, "languageTags" : languageTags, "miscTags" : miscTags }  
        return tags
            
    def moveRom(rom, tags):
        usaPath = extPath + "/USA"
        eurPath = extPath + "/Europe"
        jpnPath = extPath + "/Japan"
        worPath = extPath + "/World"
        #print("DEBUG: eurPath is", eurPath, type(eurPath), "jpnPath is", jpnPath, type(jpnPath), "worPath is", worPath, type(worPath),  )
    
        # Match by region  
        if tags["regionTags"]:                                      # If regionTags dictionary entry is not empty
            if "USA" in regionTags or tag in romRegion["USA"]:                                 # Attempt to bail out early by matching on master sort region
                print("DEBUG: *** Moved rom to", sortRegion, "folder ***")
                os.replace(extPath + "/" + rom, usaPath + "/" + rom)
                return 0
            elif "Japan*" in tags["regionTags"] or tag in romRegion["Japan"]:
                os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                print("DEBUG: *** Moved rom to", jpnPath, " ***")
                return 0
            elif "Europe" in tags["regionTags"] or tag in romRegion["Europe"]:
                os.replace(extPath + "/" + rom, eurPath + "/" + rom)
                print("DEBUG: *** Moved rom to", eurPath, " ***")
                return 0
            elif tags["regionTags"] is "World" and if not tags["languageTags"] or "En" in tags["lanaguageTags"]:
                print("DEBUG: *** ROM LEFT IN ROOT FOLDER WORLD ***")
                return 1
            elif tag in romRegion["World]:
                os.replace(extPath + "/" + rom, worPath + "/" + rom)
                print("DEBUG: *** Moved rom to", worPath, " ***")
                return 0              
            # If unknown region
            else:
                if tags["languageTags"] and "En" not in tags["languageTags']:
                    os.replace(extPath + "/" + rom, worPath + "/" + rom)
                    print("DEBUG: *** Moved unmatched foreign language rom to", worPath, " ***")
                    return 0
                else
                    ("DEBUG: *** UNMATCHED ROM LEFT IN ROOT ***")
                    return 1
        elif "En" in tags["languageTags"]:
            ("DEBUG: *** REGIONLESS En ROM LEFT IN ROOT ***")
            return 1
        else:
            ("DEBUG: *** UNMATCHED ROM LEFT IN ROOT ***")
            return 1
                
                
                for tag in tags["regionTags"]:                          # For each of the collected region tags
                    print("DEBUG: working on tag:", tag, type(tag)) 
                    print("DEBUG: regions is:", regions, type(regions)) 
                    if tag in romRegion["USA"]:
                        print("DEBUG: *** ROM LEFT IN ROOT FOLDER USA ***")
                        return 1
                    elif tag in romRegion["Japan"]:
                        os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                        print("DEBUG: *** Moved rom to", jpnPath, " ***")
                      ion["Europe"]:  return 0   
                    elif tag in romRegion["Europe"]:
                        os.replace(extPath + "/" + rom, eurPath + "/" + rom)
                        print("DEBUG: *** Moved rom to", eurPath, " ***")
                        return 0
                    elif tag in romRegion["World"]:
                        os.replace(extPath + "/" + rom, worPath + "/" + rom)
                        print("DEBUG: *** Moved rom to", worPath, " ***")
                        return 0
                    else:
                        ("DEBUG: *** UNMATCHED ROM LEFT IN ROOT ***")
                        return 1 
                   
                   
                   # If the tag matches one of the master sort regions
                    if tag in romRegion.keys():
                        for sortRegion in romRegion:            # For each of the general region folders in romRegion dict
                            print("DEBUG: sortRegion is", sortRegion, type(sortRegion), "tag is", tag, type(tag))
                            if sortRegion in tag:
                                if sortRegion is "USA" or "USA" in regionTags:
                                    print("DEBUG: *** Moved rom to", sortRegion, "folder ***")
                                    os.replace(extPath + "/" + rom, usaPath + "/" + rom)
                                    return 0
                                elif sortRegion is "Europe":
                                    os.replace(extPath + "/" + rom, eurPath + "/" + rom)
                                    print("DEBUG: *** Moved rom to", eurPath, " ***")
                                    return 0
                                elif sortRegion is "Japan":
                                    os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                                    print("DEBUG: *** Moved rom to", jpnPath, " ***")
                                    return 0       
                                elif sortRegion is "World":
                                    if len(tags) == 1:
                                        os.replace(extPath + "/" + rom, worPath + "/" + rom)
                                        print("DEBUG: *** Moved rom to", worPath, " ***")
                                        return 0
                                    else:
                                        if processLang(rom, tags) == 0:
                                            os.replace(extPath + "/" + rom, worPath + "/" + rom)
                                            print("DEBUG: *** Moved rom to", worPath, " ***")
                                            return 0
                                        else:
                                            return 1
                            else:           # If current sortRegion being checked does not match rom tag
                                continue    # Continue to next sortRegion
                    else:                   # If tag is not a direct match for a master sortRegions
                        # If after moving through each of the folder regions, the tag as not been matched    
                        print("DEBUG: working on tag by romRegion:", tag, type(tag))
                        print("DEBUG: romRegion.values():", romRegion.values(), type(romRegion.values()))
                        if tag in romRegion["USA"]:
                            print("DEBUG: *** ROM LEFT IN ROOT FOLDER USA ***")
                            return 1
                        elif tag in romRegion["Japan"]:
                            os.replace(extPath + "/" + rom, jpnPath + "/" + rom)
                            print("DEBUG: *** Moved rom to", jpnPath, " ***")
                            return 0   
                        elif tag in romRegion["Europe"]:
                            os.replace(extPath + "/" + rom, eurPath + "/" + rom)
                            print("DEBUG: *** Moved rom to", eurPath, " ***")
                            return 0
                        elif tag in romRegion["World"]:
                            os.replace(extPath + "/" + rom, worPath + "/" + rom)
                            print("DEBUG: *** Moved rom to", worPath, " ***")
                            return 0
                        else:
                            ("DEBUG: *** UNMATCHED ROM LEFT IN ROOT ***")
                            return 1        
                        
    def processLang(rom, tags):
        #langTags = tags
        #print("DEBUG: langTags are", langTags, type(langTags))
        #langTags = langTags.split(',')
        #print("DEBUG: langTags after split are", langTags, type(langTags))
        for langTag in tags["languageTags"]:                                                    # Loop through each of the languages stored in romLang tuple
            print("DEBUG: checking for langTag", langTag, type(langTag))
            if langTag in romLang:
                print("DEBUG: entered world lang")
                if langTag is "En":                                                   # If the language is En, then leave it in root directory
                    print("DEBUG: *** Left rom in", folder, "folder ***")                                                          # Break out of the function and move to the next rom 
                    return 1
                else:                                                                  # If the language code is something other than En
                    return 0
            else:
                print("DEBUG: langTag", langTag, "was not found in romLangs", type(langTag))
                return 1
            
    print("DEBUG: romRegion USA is", romRegion["USA"], type(romRegion["USA"]))
    print("DEBUG: romRegion[Japan] is", romRegion["Japan"], type(romRegion["Japan"]))
    print("DEBUG: romRegion[Europe] is", romRegion["Europe"], type(romRegion["Europe"]))
    print("DEBUG: romRegion[World] is", romRegion["World"], type(romRegion["World"]))
    print("DEBUG: romLang is", romLang, type(romLang))
    
    def makeDirs():
        eurPath = extPath + "/Europe"
        jpnPath = extPath + "/Japan"
        worPath = extPath + "/World"
        
        if os.path.isdir(eurPath):
            print("DEBUG: entered if eur")
            pass
        else:
            print("DEBUG: entered mkdir eur")
            os.mkdir(eurPath)
        if os.path.isdir(jpnPath):
            print("DEBUG: entered if jpn")
            pass
        else: 
            print("DEBUG: entered mkdir jpn")
            os.mkdir(jpnPath)
        if os.path.isdir(worPath):
            print("DEBUG: entered if wor")
            pass
        else: 
            print("DEBUG: entered mkdir wor")
            os.mkdir(worPath)
    
    audit = open("audit.txt", "a")
    
    makeDirs()

    for rom in os.listdir(extPath):
        print("DEBUG: WORKING ON ROM", rom, type(rom))
        if rom.endswith(".zip"):
            tags = gatherTags(rom)
            print("DEBUG: tags are:", tags, type(tags))
            results = moveRom(rom, tags)
            print("DEBUG: results of romMove is", results, type(results))
            if results != 0:
                audit.write(rom + "\n")
                print("DEBUG: *** Left in root folder ***")
        else:
            continue
    
    audit.close()
    
# BASH ENGINE: Runs commands in a bash shell
def execBash(execBash_CMD):
    global bash
    
    print("DEBUG: execbash bashCMD is", execBash_CMD)
    bash=subprocess.run(execBash_CMD, shell = True, executable = "/bin/bash", capture_output=True)
    print("DEBUG: execbash bash is", bash, type(bash))

# Defines the order subroutines are executed
def mainRoutine():
    checkZip()              # Performs sanity checks on target file
    unzip()                 # Unzips target file
    processRom()            # Processes roms based on region and language and moves them into sub-folders
    #checkConfig()          # Check if config file exists, if not create it
    #checkHost()            # Check if remote made is already awake
    #wakeHost()             # Wakes the remote machine using etherwake
    #connectSSH()           # Establishes a ssh connect with the remote machine
    exit(0)
	
# Calls the main routine on script startup
mainRoutine()               # Script entry point; execution begins here
