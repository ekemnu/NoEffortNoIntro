from pathlib import Path        # Used to perform os independent path manipulation


def chkTargetsTEST(targets, msg):    
    m = msg
    tgtList = []
    
    m.st("Checking target archive...")
    for target in targets:
        target = Path(target)
        # Check to see if the target is a file or directory
        # Check to see if target is a valid file
        if target.is_file():
            # Target was a file, add it to the target list
            m.de("is file")
            tgtList.append(target.resolve())
            continue
        # If the target wasn't a file, was it a directory?
        elif target.is_dir():
            tgtList.extend = [ f for f in target.glob('*.zip', case_sensitive=None) ]
            m.de("is dir")
            # Target is a directory, scan it for archives
            m.st("Gathering Archives From Source Directory...")
            for tgtFile in tgtList:
                m.st("Discovered", tgtFile.name, "in Target Directory")
            continue
        else:
            # Error if the target was neither a file or directory
            m.er("Target File or Directory Cannot Be Found")
            m.ei("Please supply a valid path to either a single, or a directory with No-Intro archives and run NeNi again")
            m.ei("  Ex: $ neni /home/user/Downloads/archive.zip")
            m.ei("  or: $ neni /home/user/Downloads/NoIntroArchives")
            m.ex("Error")
            sys.exit(1)
    # Return the list of full paths to the targets
    return tgtList