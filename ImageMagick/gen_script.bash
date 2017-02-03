#!/bin/bash

if [ -z ${1} ] || [ -z ${2} ] || [ -z ${3} ] || [ -z ${4} ]; then
    echo "missing params"
    echo "${0} size count outputdir script"
    exit
fi
   
if [ ! -e ${4} ]; then
    echo "file not found: ${4}"
    exit
fi
    
size=${1}
count=${2}
output_dir=${3}

scripts_dir="scripts"

script_file_name=$(basename ${4})
script_name=${script_file_name%.*}
out=${output_dir}/${script_name}_${size}_${count}
for i in $(seq -w ${count})
    do
        ${4} ${size} ${out} ${i}
    done

exit $?
