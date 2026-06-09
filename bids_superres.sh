#!/usr/bin/bash

# set -x 

module load c3d
module load python

SRPATH="/project/wolk_4/naccsc_bids/scripts/adni_processing_pipeline/utilities/build_release"
echo Script versions: 
echo $SRPATH
which c3d
# which python

# inputs
input_file=$1
output_directory=$2

## set output file name
# sr_bids_entity='{"desc":"superres"}'
# output_file_name=$( python /project/wolk_4/naccsc_bids/scripts/picsl_bids_pipeline/bids_file_names.py -i $(basename $input_file) -o $sr_bids_entity)
output_file_name=$( basename $input_file | sed 's/desc-preproc/desc-superres/' )
final_sr_output_filepath="${output_directory}/${output_file_name}"
echo Output image will be stored as: $final_sr_output_filepath

if [[ -f $final_sr_output_filepath ]] ; then 
    echo Output file already exists, exiting
    exit 0
fi 

## make this run script part of SRpath package? 
## make singularity container from SRPATH -- Long & Paul were the ones who wrote it? 

## Run in tmpdir, always remove tmpdir when script exits
tmpdir=$( mktemp -d --tmpdir=/scratch )
echo Running in $tmpdir
trap "rm -rf $tmpdir" EXIT

$SRPATH/NLMDenoise \
    -i $input_file \
    -o $tmpdir/T1w_trim_denoised.nii.gz

c3d $tmpdir/T1w_trim_denoised.nii.gz \
    -swapdim RPI \
    -o $tmpdir/T1w_trim_denoised.nii.gz

$SRPATH/NLMUpsample \
    -i $tmpdir/T1w_trim_denoised.nii.gz \
    -o $tmpdir/T1w_trim_denoised_SR.nii.gz \
    -lf 2 1 2

orient_code=$(c3d $input_file -info | cut -d ';' -f 5 | cut -d ' ' -f 5)
if [[ $orient_code == "Oblique," ]]; then
    orient_code=$(c3d $input_file -info | cut -d ';' -f 5 | cut -d ' ' -f 8)
fi

c3d $tmpdir/T1w_trim_denoised_SR.nii.gz\
    -swapdim $orient_code \
    -clip 0 inf \
    -type short \
    -o $final_sr_output_filepath

## Add info to json file for output
today_date=$( date +"%Y-%m-%d" )
json_version_bids_dir_name="NACC-SC_BIDS" ## get from bids/ dir dataset_description.json "Name" field
json_version_input_file=$inputfile ##input filepath from sub- level including file name
# /project/wolk_4/naccsc_bids/bids/derivatives/T1wPreprocessing_061/sub-131378/ses-131378x20250410x3TxABCD2/anat/sub-131378_ses-131378x20250410x3TxABCD2_acq-800um_desc-preproc_T1w.nii.gz

output_json=$( echo $final_sr_output_filepath | sed 's/.nii.gz/.json/' )
jq -n --arg "Script" $SRPATH --arg "ProcessDate" $today_date \
        --arg "Sources" "bids:${json_version_bids_dir_name}:${json_version_input_file}" \
        '{"Script": $Script, "ProcessDate": $ProcessDate, "Sources":[$Sources]}'  >> $output_json

