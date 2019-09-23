##################################################
# File  Name: export_text.sh
#     Author: shwin
# Creat Time: Wed Aug 14 14:00:42 2019
##################################################

#!/bin/bash

count=0
touch "URI.txt"
while read line
do
    name=$(echo $line | awk -F ':' '{print$1}')
    ((count+=1))
    echo $count $name
    # echo $name" :" >> "URI.txt"
    printf '%20s: \n' $name >> "URI.txt"
done < description.txt
