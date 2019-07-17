##################################################
# File  Name: export_svg.sh
#     Author: shwin
# Creat Time: Wed Jul 17 19:40:49 2019
##################################################

#!/bin/bash

if [ -z "$1" ];then
    echo "No file specified!"
    exit 1
fi

fileName=$1
baseName=${fileName%.*}
echo $baseName
exDirName="m_$baseName"
if [ -d $exDirName ];then
    cd $exDirName && rm *
    cd ..
else
    mkdir $exDirName
fi

./svg-objects-export/svg-objects-export.py $(pwd)/$fileName -d $(pwd)/$exDirName/ --pattern '^A-' --extra " --export-id-only" --prefix ''
