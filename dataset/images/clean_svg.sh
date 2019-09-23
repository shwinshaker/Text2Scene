##################################################
# File  Name: clean_svg.sh
#     Author: shwin
# Creat Time: Fri Aug 30 14:34:50 2019
##################################################

#!/bin/bash
# https://stackoverflow.com/questions/6287755/using-sed-to-delete-all-lines-between-two-matching-patterns
sed '/<image/,/\/image>/d' play_time.svg > play_time_test2.svg
sed '/<i:pgf.*>/,/<\/i:pgf.*>/{/<i:pgf.*>/!{/<\/i:pgf.*>/!d;};}' play_time_test2.svg > play_time_test3.svg
