##################################################
# File  Name: rename.sh
#     Author: shwin
# Creat Time: Thu Jul 25 20:53:13 2019
##################################################

#!/bin/bash
targetDir='../../images'
suffix='.svg'
last=$(ls $targetDir/*$suffix | awk -F '/' '{print$NF}' | sort -n | tail -1)
lastId=${last%"$suffix"}
echo "last ID: $lastId"
for file in $(ls *$suffix | sort -n); do
    id=${file%.*}
    newId=$(($id+$lastId))
    echo 'id: '$id' - new id: '$newId
    mv $file $targetDir/"$newId"$suffix
done
