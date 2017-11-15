#!/bin/bash

# Script to down sample NIH X-Ray dataset at https://www.kaggle.com/nih/xray1-2  [3-4, 5-6, 7-8, 9-10, 11-12]
# Randomly samples 5% of images from the 12 zip files

function get_file_count(){
  file_name=$1
  # Given a zip file name return a count of the files inside
  unzip -l "$file_name" | grep -c png
}

function get_sample_size(){
  # Given number of files calculate the sample size (5% of all files)
  python -c "print(round($1 * 0.05))"
}

function extract_sample_size_names(){
  file_name=$1
  sample_size=$2
  # Given a zip file and sample size, create a random list of file names in the zip file
  unzip -l "$file_name" | grep png | shuf -n "$sample_size" | sed 's/   /,/g' | cut -d , -f 3
}


for file in *.zip; do
  num_files=$(get_file_count $file)
  sample_size=$(get_sample_size $num_files)
  unzip $file $(extract_sample_size_names $file $sample_size)
done

