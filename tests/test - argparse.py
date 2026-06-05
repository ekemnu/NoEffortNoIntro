from pathlib import Path        # Used to perform os independent path manipulation
from neni import argParser      # Function being tested

testLocation = "/home/john/Documents/Code/No Effort No Intro/tests/checktarget_testcases/checktargets_test"

# Tests setting no targets being passed
print(f"\n---- Begining Test 'No Target' ----")
arguments = [ ]
try:
    flags = argParser(arguments)
except ValueError as e:
    print(f"Returned: ValueError {e}\n"
          f"Expected: ValueError")
    print("Test completed sucessfully")
else:
    raise ValueError (print(f"Returned: NoError\n"
                            f"Expected: ValueError"))

# Tests targeting an archive
print(f"\n---- Begining Test 'target' ----")
arguments = [ f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip" ]
expected  = [ Path(testLocation, "Archive - With 3 Top Level Games (Normal Set).zip") ]
flags = argParser(arguments)
print(f"Returned: {flags.targets}\n"
      f"Expected: {expected}")
assert flags.targets == expected
print("Test completed sucessfully")

# Tests targeting an multiple archives
print(f"\n---- Begining Test 'multitarget' ----")
arguments = [ f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip",
              f"{testLocation}/Archive - With 3 Top Level Games (Normal Set)2.zip" ]
expected  = [ Path(testLocation, "Archive - With 3 Top Level Games (Normal Set).zip").resolve(),
              Path(testLocation, "Archive - With 3 Top Level Games (Normal Set)2.zip").resolve() ]
flags = argParser(arguments)
print(f"Returned: {flags.targets}\n"
      f"Expected: {expected}")
assert flags.targets == expected
print("Test completed sucessfully")

# Tests enabling debug mode
print(f"\n---- Begining Test '--debug' ----")
arguments = [ "--debug", f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip" ]
expected  = True
flags = argParser(arguments)
print(f"Returned: {flags.debug}\n"
      f"Expected: {expected}")
assert flags.debug == expected
print("Test completed sucessfully")

# Tests enabling pretnd mode
print(f"\n---- Begining Test '--pretend' ----")
arguments = [ "--pretend", f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip" ]
expected  = True
flags = argParser(arguments)
print(f"Returned: {flags.ptend}\n"
      f"Expected: {expected}")
assert flags.ptend == expected
print("Test completed sucessfully")

# Tests setting a relase string
print(f"\n---- Begining Test '--release' ----")
arguments = [ "--release", "20260101-5467844", f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip" ]
expected  = "20260101-5467844"
flags = argParser(arguments)
print(f"Returned: {flags.relVers}\n"
      f"Expected: {expected}")
assert flags.relVers == expected
print("Test completed sucessfully")

# Tests setting skip extraction mode target
print(f"\n---- Begining Test '-x' ----")
arguments = [ "-x", f"{testLocation}/directory_with_games" ]
expected  = [ Path(testLocation, "directory_with_games").resolve() ]
flags = argParser(arguments)
print(f"Returned: {flags.sXtrct}\n"
      f"Expected: {expected}")
assert flags.sXtrct == expected
print("Test completed sucessfully")

# Tests setting multiple skip extraction mode targets
print(f"\n---- Begining Test '-x -x' ----")
arguments = [ "-x", f"{testLocation}/directory_with_games",
              "-x", f"{testLocation}/directory_with_junk" ]
expected  = [ Path(testLocation, "directory_with_games").resolve(),
              Path(testLocation, "directory_with_junk").resolve() ]
flags = argParser(arguments)
print(f"Returned: {flags.sXtrct}\n"
      f"Expected: {expected}")
assert flags.sXtrct == expected
print("Test completed sucessfully")

# Tests setting skip extraction target with normal target
print(f"\n---- Begining Test '-x', 'target' ----")
arguments   = [ "-x", f"{testLocation}/directory_with_games",
                f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip" ]
expected    = [ Path(testLocation, "directory_with_games").resolve() ]
expectedTgt = [ Path(testLocation, "Archive - With 3 Top Level Games (Normal Set).zip").resolve() ]
flags = argParser(arguments)
print(f"sXtrct:\n"
      f"Returned: {flags.sXtrct}\n"
      f"Expected: {expected}\n"
      f"target:\n"
      f"Returned: {flags.targets}\n"
      f"Expected: {expectedTgt}")
assert flags.sXtrct == expected
assert flags.targets == expectedTgt
print("Test completed sucessfully")

# Tests setting a home region
print(f"\n---- Begining Test '--home-turf' ----")
arguments = ["-t", "Europe", f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip" ]
expected  = "Europe"
flags = argParser(arguments)
print(f"Returned: {flags.homeRgn}\n"
      f"Expected: {expected}")
assert flags.homeRgn == expected
print("Test completed sucessfully")

# Tests setting a bad home region
print(f"\n---- Begining Test '--home-turf BAD' ----")
arguments = ["-t", "Stanktopia", f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip" ]
try:
    flags = argParser(arguments)
except ValueError as e:
    print(f"Returned: ValueError {e}\n"
          f"Expected: ValueError")
    print("Test completed sucessfully")
else:
    raise ValueError (print(f"Returned: NoError\n"
                            f"Expected: ValueError"))

# Tests setting a language
print(f"\n---- Begining Test '--language' ----")
arguments = ["-l", "Fr", f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip"]
expected  = "Fr"
flags = argParser(arguments)
print(f"Returned: {flags.language}\n"
      f"Expected: {expected}")
assert flags.language == expected
print("Test completed sucessfully")

# Tests setting a bad language
print(f"\n---- Begining Test '--langauge BAD' ----")
arguments = ["-l", "Kl", f"{testLocation}/Archive - With 3 Top Level Games (Normal Set).zip" ]
try:
    flags = argParser(arguments)
except ValueError as e:
    print(f"Returned: ValueError {e}\n"
          f"Expected: ValueError")
    print("Test completed sucessfully")
else:
    raise ValueError (print(f"Returned: NoError\n"
                            f"Expected: ValueError"))