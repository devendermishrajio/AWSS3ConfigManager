#!/bin/bash
upload() {
  filename=$(basename $2)
  ext="${filename##*.}"
  fname="${filename%.*}"
  python uploadFileToS3.py "staging-log-dir" "$1/`hostname`/$fname-`date +'%Y%d%m'`.$ext" $2
}

fname=$2
file_list=`find $1`
for i in $file_list; do
  if [ -f $i ]; then
    upload $fname $i
  fi
done

