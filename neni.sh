#!/bin/bash

# Extracts and proccess downloaded No-Intro Rom archives
#	Sorts Roms by region and language into subfolders 
# Written by John Loreth 2024

# Parameter Handling
echo input is "$@"
PARAM="$( echo "$@" )"															# Set runtime parameters as a variable	  
echo param is "$PARAM"
ZIP="$( echo "$PARAM" | sed 's/.*\///' )"	  									# Remove everything before final / to get archive name
echo zip is "$ZIP"
WPATH="$( echo "$PARAM" | sed 's|\(.*\)/.*|\1|' )" 								# Get the path to the file from the param
echo path is "$WPATH"
DIR="$( echo "$PARAM" | cut -d '.' -f 1 )"		  								# Get the Directory to extract to
echo dir is "$DIR"

# Unzip the downloaded Rom File
if [[ -e "$PARAM" ]] && [[ "$ZIP" == *zip ]] ; then								# IF the file specified exsists and is a zip file
	echo "entered unzip"
	unzip '-d' "$DIR" "$WPATH"'/'"$ZIP"											# Unzip the archive into a folder that matches archive name
else																			# If the file specified doesn't exisit or isn't a zip
	echo "File "$ZIP" cannot be found or is not a zip archive"
	exit 1																		# Exit with an error
fi

if find "$DIR" -mindepth 1 -maxdepth 1 | read ; then							# Check if folder exsists are is empty
	echo entered move
	mkdir "$DIR"/Japan "$DIR"/Europe "$DIR"/World								# Create region folders
	for ROM in "$DIR"\/* ; do													# Loop through every file in the unzip target directory
		echo "file is $ROM"
		if [[ "$ROM" == *\(*USA*\)* ]] || [[ "$ROM" == *\[BIOS\]* ]] ; then		# For performance, handle USA roms first, leave them in root
			continue
		elif [[ "$ROM" == *\(World* ]] ; then									# If Rom is from region "World"
			echo entered world
			if [[ "$ROM" != *\(World\)*\(En*\)* ]] ; then						# Leave english World Roms in root
				if [[ "$ROM" == *\(World\)*\(Ja\)* ]] || \						# Japanese
			       [[ "$ROM" == *\(World\)*\(Fr\)* ]] || \						# French
				   [[ "$ROM" == *\(World\)*\(Es\)* ]] || \						# Spanish
				   [[ "$ROM" == *\(World\)*\(De\)* ]] || \						# German
				   [[ "$ROM" == *\(World\)*\(Pl\)* ]] || \						# Polish
				   [[ "$ROM" == *\(World\)*\(Fi\)* ]] || \						# Finnish
				   [[ "$ROM" == *\(World\)*\(Pt\-BR\)* ]] || \					# Brazalian Portugese
				   [[ "$ROM" == *\(World\)*\(Sv\)* ]] || \						# Solvenian
				   [[ "$ROM" == *\(World\)*\(Pt\)* ]] || \						# Portugese
				   [[ "$ROM" == *\(World\)*\(Ca\)* ]] || \						# Caladonian
				   [[ "$ROM" == *\(World\)*\(Nl\)* ]] || \						# Netherlands
				   [[ "$ROM" == *\(World\)*\(Kw\)* ]] || \						# Cornish
				   [[ "$ROM" == *\(World\)*\(It\)* ]] || \						# Italian
				   [[ "$ROM" == *\(World\)*\(Zh\)* ]] || \						# Chinese
				   [[ "$ROM" == *\(World\)*\(Ko\)* ]] || \						# Korean
				   [[ "$ROM" == *\(World\)*\(El\)* ]] || \						# Greek
				   [[ "$ROM" == *\(World\)*\(Pt-PT\)* ]] || \					# Portugese
				   [[ "$ROM" == *\(World\)*\(Es-XL\)* ]] || \					# Latin America Spanish
				   [[ "$ROM" == *\(World\)*\(Ru\)* ]] ; then					# Russian
					echo entered world foreign lgn
					mv "$ROM" "$DIR"/World										# Move the file to World/
				elif [[ "$ROM" == *\(PAL\)* ]] ; then							# If the file is world region and PAL
					echo entered WORLD PAL Europe
					mv "$ROM" "$DIR"/Europe										# Move to Europe/
				else															# If the rom doesn't match a foreign language, and is not PAL
					echo entered world continue
					continue													# Leave it in root
				fi
			else
				echo entered world lng en continue
				continue														# If the World region Rom doesn't give a lanaguage leave it in root
			fi
		elif [[ "$ROM" == *\(Japan*\)* ]] ; then 								# If the Rom is Japan region
			echo entered Japan
			mv "$ROM" "$DIR"/Japan												# Move to Japan/
		elif [[ "$ROM" == *\(Asia\)* ]] || \									# If the Rom is Asia region or
		     [[ "$ROM" == *\(China\)* ]] ; then									# If the Rom is China region
			echo entered world
			mv "$ROM" "$DIR"/World 												# Move to World/
		elif [[ "$ROM" == *\(Europe*\)* ]] ; then								# If the Rom is Europe region
			echo entered Europe
			mv "$ROM" "$DIR"/Europe												# Move to Europe/
		elif [[ "$ROM" == *\(Korea*\)* ]] || \									# World/ region handling
		     [[ "$ROM" == *\(Australia*\)* ]] || \
		     [[ "$ROM" == *\(Spain*\)* ]] || \
		     [[ "$ROM" == *\(France*\)* ]] || \
		     [[ "$ROM" == *\(Germany*\)* ]] || \
		     [[ "$ROM" == *\(Taiwan\)* ]] || \
		     [[ "$ROM" == *\(Italy*\)* ]] || \
		     [[ "$ROM" == *\(Argentina*\)* ]] || \
		     [[ "$ROM" == *\(Hong\ Kong*\)* ]] || \
		     [[ "$ROM" == *\(Brazil*\)* ]] || \
		     [[ "$ROM" == *\(Latin\ America*\)* ]] || \
		     [[ "$ROM" == *\(Sweden*\)* ]] || \
		     [[ "$ROM" == *\(Russia*\)* ]] || \
		     [[ "$ROM" == *\(Unknown\)\ \(Ja\)* ]] || \
		     [[ "$ROM" == *\(Unknown\)\ \(De\)* ]] || \
		     [[ "$ROM" == *\(Unknown\)\ \(En\)* ]] || \
		     [[ "$ROM" == *\(Unknown\)\ \(Fr\)* ]] || \
		     [[ "$ROM" == *\(Unknown\)\ \(It\)* ]] || \
		     [[ "$ROM" == *\(Unknown\)\ \(Pt\)* ]] || \
		     [[ "$ROM" == *\(Unknown\)\ \(Es\)* ]] || \
		     [[ "$ROM" == *\(Unknown\)*\(PAL\)* ]] || \
		     [[ "$ROM" == *\(Canada\)\ \(Fr\)* ]] ; then
			echo entered misc
			mv "$ROM" "$DIR"/World												# If Rom matches one of above regions, move to World/
		elif [[ "$ROM" == *\(Scand*\)\ \(En\)* ]] || \							# If rom matches one of these rare regions
		     [[ "$ROM" == *\(United\ Kingdom\)* ]] ; then
			echo entered Europe
			mv "$ROM" "$DIR"/Europe												# Move to Europe
		else
			echo entered move continue											# If Rom has no match, leave it in root
			continue
		fi
	done
else
	echo entered empty															# If unzip target directory is empty
	exit 1																		# Exit with error
fi

echo '### CHECK BEGINING ###'
echo '     THE BELOW FILES WHICH ARE NOT USA REMAIN'
for ROM in "$DIR"\/* ; do
	if [[ "$ROM" != *\(*USA*\)* ]] && [[ "$ROM" != *\(World\)*\(En* ]] ; then
		echo "$ROM"
	else
		continue
	fi
done
