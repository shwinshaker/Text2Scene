##################################################
# File  Name: export_text.sh
#     Author: shwin
# Creat Time: Wed Aug 14 14:00:42 2019
##################################################

#!/bin/bash

while read line
do
    name=$(echo $line | awk -F ':' '{print$1}')
    if [ -e "$name.svg" ];then
	echo $name
	text=$(echo $line | awk -F ':' '{print$2}')
	echo $text > "../text/$name.txt"
    else
	echo "\033[0;31mError! Bad identifier: $name\033[0;00m"
	exit -1
    fi
done < description.txt
