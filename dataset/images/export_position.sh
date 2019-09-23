##################################################
# File  Name: export_text.sh
#     Author: shwin
# Creat Time: Wed Aug 14 14:00:42 2019
##################################################

#!/bin/bash

inkscape="/Applications/Inkscape.app/Contents/Resources/bin/inkscape"
dest_dir='position'
for svg in *.svg
do
    basename=$(echo $svg | awk -F '.' '{print$1}')
    echo $basename
    $inkscape $(pwd)/$svg -S > $dest_dir/$basename".txt"
done
