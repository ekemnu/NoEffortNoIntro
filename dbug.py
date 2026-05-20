#####   Debug Tools
#####	John Loreth
#####	2024
#####	v0.11
#####
#####   A Collection of debug tools
#####
#####   Version history:
#####		0.1  Added a debug messgage buffer

class color:
   p = '\033[95m'      # Purple
   dc = '\033[96m'        # Cyan
   dc = '\033[36m'    # Dark Cyan
   b = '\033[94m'        # Blue
   g = '\033[92m'       # Green
   y = '\033[93m'      # Yellow
   r = '\033[91m'         # Red
   b = '\033[1m'         # Bold
   u = '\033[4m'    # Underline
   o = '\033[0m'          # off
        
class dc:
    # Debug Colors
    g = '\033[0m' + '\033[92m'                  # Off and Green 
    gb = '\033[0m' + '\033[92m' + '\033[1m'     # Off and Green and bold
    gu = '\033[0m' + '\033[92m' + '\033[4m'     # Off and Green and underline
    # Style
    b = '\033[1m'    # Bold
    u = '\033[4m'    # Underline
    o = '\033[0m'    # off

class dbmsg():

    # Takes general debug messages and prints the result
    # pt.ds(string)
    def ds(*dsMsg):
        print("NeNI:", dc.b + "DEBUG:", dc.gb + ' '.join((dsMsg[:])) + dc.o)
        
    # Prints working on rom mesages
    # pt.dr
    def dp(dpRom, *dpSkip):
        if not dpSkip:
            print("NeNI:", dc.b + "DEBUG:", dc.gb + "Processing " + dc.o + "file", dc.gb + dpRom, dc.o + "...")
        else:
            print("NeNI:", dc.b + "DEBUG:", dc.gb + "Processing " + dc.o + "file", dc.gb + dpRom, dc.o + "...")
    
    # dvVar = [ [variable] , [variable name]]
    # pt.dv( [ "var1", "var2 in", "var3", "var4", ... ], [ var1, var2, var3, var4, ... ] ]
    # pt.dv( { "var1": var1, "var2 in": var2, "var3 blah": var3, "var4": var4, ... } )
    # pt.dv( {"var1":var1})
            
    # Takes a list of variables and prints them with their values and types
    def dv(dvGlob, *dvVar):
        for var in dvVar:
            print("NeNI:", dc.b + "DEBUG:", dc.gb + str(var), dc.o + "is:", dc.gb + str(dvGlob[var]) + dc.o + " " + str(type(dvGlob[var])))
    
    # Prints a debug message with a string for a location to mark entering sections of code
    # pt.de(location) > " NeNI: DEBUG: Entered location "
    def de(deLoc):
        print("NeNI:", dc.b + "DEBUG:", dc.b + "Entered", dc.gb + str(deLoc) + dc.o)
