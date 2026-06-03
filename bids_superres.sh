#!/usr/bin/bash

module load c3d
module load python

# inputs
input_file=$1
output_directory=$2

## set output file name
sr_bids_entity='{"desc":"superres"}'
output_file_name=$( python /project/wolk_4/naccsc_bids/scripts/picsl_bids_pipeline/bids_file_names.py -i $(basename $input_file) -o $sr_bids_entity)
final_sr_output_filepath="${output_directory}/${output_file_name}"
echo 
echo
# echo $output_file_name
echo $final_sr_output_filepath

## use tmp dir for intermediate files, then only copy over final file (check with Sandy that the intermediate files aren't needed)
## make this run script part of SRpath package? 
# make singularity container from SRPATH -- Long & Paul were the ones who wrote it? 

SRPATH="/project/wolk_4/naccsc_bids/scripts/adni_processing_pipeline/utilities/build_release"
echo Script versions: 
echo $SRPATH
which c3d
which python

# $SRPATH/NLMDenoise \
#     -i $input_file \
#     -o $output_directory/T1w_trim_denoised.nii.gz

# c3d $output_directory/T1w_trim_denoised.nii.gz \
#     -swapdim RPI \
#     -o $output_directory/T1w_trim_denoised.nii.gz

# $SRPATH/NLMUpsample \
#     -i $output_directory/T1w_trim_denoised.nii.gz \
#     -o $output_directory/T1w_trim_denoised_SR.nii.gz \
#     -lf 2 1 2

# orient_code=$(c3d $input_file -info | cut -d ';' -f 5 | cut -d ' ' -f 5)
# if [[ $orient_code == "Oblique," ]]; then
#     orient_code=$(c3d $input_file -info | cut -d ';' -f 5 | cut -d ' ' -f 8)
# fi

# c3d $output_directory/T1w_trim_denoised_SR.nii.gz\
#     -swapdim $orient_code \
#     -clip 0 inf \
#     -type short \
#     -o $final_sr_output_file
