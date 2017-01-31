#!/bin/bash

if [ -z $1 ] || [ -z ${2} ] || [ -z ${3} ]; then
    echo "missing params..."
    echo "${0} size outputdir filename"
    exit $?
fi

size_y=${1}
size_y_double=$(( ${size_y}*2 ))
size_x=$(printf "%.0f" $(echo "${size_y}*1.6" | bc))
size_x_half=$(( ${size_x}/2 ))
output_dir=${2}
file_name=${3}

if [ ! -d ${output_dir} ]; then
    mkdir -p ${output_dir}
fi

tmpfile=$(mktemp --suffix .png)

convert -size ${size_y}x${size_x} xc: +noise Random -write mpr:rand \
        -extent ${size_y_double}x${size_x} -page +${size_y}-${size_x_half} mpr:rand \
        -page +${size_y}+${size_x_half} mpr:rand -flatten ${tmpfile}
convert ${tmpfile} -virtual-pixel tile -blur 0x10 -emboss 4 -edge 1 -auto-level ${output_dir}/${file_name}.png

rm ${tmpfile}
exit $?

