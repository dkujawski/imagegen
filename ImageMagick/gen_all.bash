#!/bin/bash

if [ -z ${1} ] || [ -z ${2} ] || [ -z ${3} ]; then
    echo "missing params"
    echo "${0} size count outputdir"
    exit
fi
    
size=${1}
count=${2}
output_dir=${3}

scripts_dir="scripts"

for s in ${scripts_dir}/*.bash
    do
        script_file_name=$(basename $s)
        script_name=${script_file_name%.*}
        out=${output_dir}/${script_name}_${size}_${count}
        for i in $(seq -w ${count})
            do
                ${s} ${size} ${out} ${i}
            done
    done

exit $?
