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

function create_zip(){
  zip sample.zip images/*
}

function create_labels(){
  # Find matching file names in $temp_file and $all_labels and create sample_labels.csv
  all_labels=$1
  temp_file=temp.txt
  ls -1 images > $temp_file
  awk -F, 'NR==FNR {a[$0];next} $1 in a' $temp_file $all_labels > sample_labels.csv'
  rm $temp_file
}

for file in *.zip; do
  num_files=$(get_file_count $file)
  sample_size=$(get_sample_size $num_files)
  unzip $file $(extract_sample_size_names $file $sample_size)
  create_zip
  create_labels Data_Entry_2017.csv 
done


