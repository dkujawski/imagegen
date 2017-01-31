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

convert -size ${size}x${size}  plasma:fractal ${tmpfile}    
convert ${tmpfile} -blur 0x5 -normalize -fx g \
        -sigmoidal-contrast 15x50% -solarize 50% \
        -shave 20x20 +repage ${output_dir}/${file_name}.png

rm ${tmpfile}
exit $?

