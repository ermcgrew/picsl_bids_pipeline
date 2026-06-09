#!/usr/bin/bash

# set -x 

## inputs:
input_file=$1
final_sr_output_filepath=$2

module load c3d
SRPATH="/project/wolk_4/naccsc_bids/scripts/adni_processing_pipeline/utilities/build_release"

echo Script versions: 
echo $SRPATH
which c3d

## Run in tmpdir
tmpdir=$( mktemp -d --tmpdir=/scratch )
echo Running in $tmpdir
## always remove tmpdir when script exits
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