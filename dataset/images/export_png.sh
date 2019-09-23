##################################################
# File  Name: export_text.sh
#     Author: shwin
# Creat Time: Wed Aug 14 14:00:42 2019
##################################################

#!/bin/bash

###############################
# error encountered when <!entity included in plain-svg
###############################

for svg in *.svg
do
    basename=$(echo $svg | awk -F '.' '{print$1}')
    echo $basename
    cairosvg $svg -o $basename".png"
done
