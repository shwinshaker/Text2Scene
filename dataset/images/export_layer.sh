##################################################
# File  Name: export_layer.sh
#     Author: shwin
# Creat Time: Fri Aug 30 15:08:34 2019
##################################################

#!/bin/bash

python2 svg-objects-export.py --pattern '^_x23_' --extra " --export-id-only" --prefix '' -t plain-svg -i /Applications/Inkscape.app/Contents/Resources/bin/inkscape -d $(pwd)/m_play_time/ $(pwd)/play_time.svg
