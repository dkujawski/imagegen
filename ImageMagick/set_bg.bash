#!/bin/bash

out=/home/dave/Pictures/background/image.png
tmpfile=$(mktemp --suffix .png)

convert -size 1920x1080 plasma:fractal ${tmpfile}    
convert ${tmpfile} -blur 0x$(( $RANDOM % 10 )) -normalize -fx 'sin(u*4*pi)*100' -edge 1 -blur 0x$(( $RANDOM % 10 )) -paint $(( $RANDOM % 20 )) -emboss $(( $RANDOM % 5 )) -fx g -sigmoidal-contrast 15x50% -solarize 50% -shave 20x20 +repage ${out}

gsettings set org.gnome.desktop.background picture-uri "file://${out}"
