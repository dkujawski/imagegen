#!/bin/bash

if [ -z $1 ] || [ -z ${2} ] || [ -z ${3} ]; then
    echo "missing params..."
    echo "${0} size outputdir filename"
    exit $?
fi

size=${1}
output_dir=${2}
file_name=${3}

if [ ! -d ${output_dir} ]; then
    mkdir -p ${output_dir}
fi

tmpfile=$(mktemp --suffix .png)

convert -size ${size}x${size} xc: +noise Random ${tmpfile}
convert ${tmpfile} -virtual-pixel tile -paint 10 -blur 0x5 -paint 10 -auto-level ${output_dir}/${file_name}.png

rm ${tmpfile}
exit $?

