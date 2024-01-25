#!/bin/bash

echo input is "$1"
FILE="$1"
echo file is "$FILE"

if [[ "$FILE" == "*zip" ]] ; then
	echo "unzip"
        unzip "$1" -d "$DIR"
else
	echo "File "$FILE" is not a zip archive"
	exit 1
fi

for ROM in "$DIR"\/\* ; do
	echo "file is $ROM"
	if [[ "$ROM" == "*\(Japan\)*" ]] ; then 
		mv "$DIR"/"$ROM" "$DIR"/Japan 
	elseif [[ "$ROM" == "*\(Europe\)*" ]] || [[ "$ROM" == "*\(Scand*\)\ \(En\)*" ]] ; then 
		mv "$DIR"/"$ROM" "$DIR"/Europe
	elseif [[ "$ROM" == "*\(France\)*" ]] || \
	   [[ "$ROM" == "*\(World\)\ \(Fr\)*" ]] || \
	   [[ "$ROM" == "*\(Germany\)*" ]] || \
	   [[ "$ROM" == "*\(World\)\ \(De\)*" ]] || \
	   [[ "$ROM" == "*\(Spain\)*" ]] || \
	   [[ "$ROM" == "*\(Italy\)*" ]] || \
	   [[ "$ROM" == "*\(Hong\ Kong\)*" ]] || \
	   [[ "$ROM" == "*\(Australia\)*" ]] || \
	   [[ "$ROM" == "*\(Korea\)*" ]] || \
	   [[ "$ROM" == "*\(China\)*" ]] || \
	   [[ "$ROM" == "*\(Brazil\)*" ]] || \
	   [[ "$ROM" == "*\(Latin\ America\)*" ]] || \
	   [[ "$ROM" == "*\(Sweden\)*" ]] || \
	   [[ "$ROM" == "*\(Canada\)\ \(Fr\)*" ]] || ; then
		mv "$DIR"/"$ROM" "$DIR"/World 
	else
		break
	fi
done
