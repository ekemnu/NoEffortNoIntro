from threading import Lock
msgLock = Lock()

##### Handles writing messages to the terminal
class messenger():
    class c:
        # Moved Colors
        c = '\033[0m' + '\033[36m'                  # Off and Dark Cyan
        cb = '\033[0m' + '\033[36m' + '\033[1m'     # Off and Dark Cyan and Bold
        cu = '\033[0m' + '\033[36m' + '\033[4m'     # Off and Dark Cyan and Underline
        yb = '\033[0m' + '\033[93m' + '\033[1m'     # Off and Yellow and Bold
        # Error Colors
        r = '\033[0m' + '\033[91m'                  # Off and red 
        rb = '\033[0m' + '\033[91m' + '\033[1m'     # Off and red and bold
        ru = '\033[0m' + '\033[91m' + '\033[4m'     # Off and red and underline
        # Style
        b = '\033[1m'    # Bold
        u = '\033[4m'    # Underline
        o = '\033[0m'    # off

    def __init__(msg, debug, verbose):
        if not verbose:
            msg.sb = msg.msgPass
            msg.ma = msg.msgPass
            msg.mv = msg.msgPass
            msg.lf = msg.msgPass
            msg.wk = msg.msgPass
        if debug:
            from dbug import dbmsg
            msg.ds = dbmsg.ds
            msg.dp = dbmsg.dp
            msg.dv = dbmsg.dv
            msg.de = dbmsg.de
    
    # Prints a preformed message to the console
    def say(msg, *line):
        with msgLock:
            print(' '.join(line))

    # Forms status messages
    # msg.st( message )
    def status(msg, *stMsg):
        msg.say("NeNI:", ' '.join(stMsg))
    # Shorthand alias for method
    st = status

    # Forms sub-status messages
    # msg.sb( message )
    def substatus(msg, *sstMsg):
        msg.say("NeNI:  ", ' '.join(sstMsg))
    # Shorthand alias for method
    sb = substatus
    
    # Forms informational notices
    # m.n( message )
    def notice(msg, *nMsg):
        msg.say("NeNI:", msg.c.yb + "NOTICE:", msg.c.o + ' '.join(nMsg))
    # Shorthand alias for method
    n = notice
    
    # Forms non-fatal warning notices
    # m.wn( message )
    def warning(msg, *wnMsg):
        msg.say("NeNI:", msg.c.yb + "WARNING:", msg.c.o + ' '.join(wnMsg))
    # Shorthand alias for method
    wn = warning
    
    # Forms Error Messages and gives advice to resolve
    # m.er([ erMsg, anything, erAdv ]) > " NeNI: ERROR: errorMessage " and " NeNI:   >>> resolveAdvice "
    def error(msg, *erMsg):
        msg.say("NeNI:", msg.c.rb + "ERROR:", msg.c.o + ' '.join(erMsg) )
    # Shorthand alias for method
    er = error
    
    # Forms informational sub error messages
    # m.ei(message)
    def errorInfo(msg, *erInfo):
        msg.say("NeNI:", msg.c.rb + "ERROR:", msg.c.o + "   >>>", ' '.join(erInfo))
    # Shorthand alias for method
    ei = errorInfo
    
    # Forms messages to notify user of current working file
    # m.wk(rom_file_name)
    def working(msg, wkRom):
        msg.say("NeNI: Working on Rom", msg.c.cb+ wkRom, msg.c.o)
    # Shorthand alias for method
    wk = working
        
    # Forms messages to notify user of file matches
    # m.mv(romName, moveLocation) > " NeNi: Moved: romName to moveLocation "
    def matched(msg, maRom, maLoc):
        msg.say("NeNI: Rom", msg.c.cb + maRom, msg.c.o + "Matched", msg.c.yb + maLoc, msg.c.o)
    # Shorthand alias for method
    ma = matched       
    
    # Forms messages to notify user of file moves
    # m.mv(romName, moveLocation) > " NeNi: Moved: romName to moveLocation "
    def move(msg, mvRom, mvLoc):
        msg.say("NeNI:   Moved", msg.c.cb + mvRom, msg.c.o + "to:", msg.c.yb + mvLoc, msg.c.o)
    # Shorthand alias for method
    mv = move
    
    def left(msg, lfRom):
        msg.say("NeNI:   Left", msg.c.cb + lfRom, msg.c.o + "in", msg.c.yb + "Root Directory", msg.c.o)
    # Shorthand alias for method
    lf = left
    
    # Forms an Exit Message
    # exit( "exit description" )
    def exit(msg, exType):
        msg.say("NeNI: Exiting on", str(exType) + "...")
    # Shorthand alias for method
    ex = exit
    
    # Skips debug messages when debug is not enabled
    def msgPass(msg, *line):
        pass
    # Shorthand alias for debug methods
    ds = msgPass
    dp = msgPass
    dv = msgPass
    de = msgPass