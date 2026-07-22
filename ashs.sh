#!/usr/bin/bash

ashs_root=$1
echo "ASHS root is ${ashs_root}"
shift
output_directory=$1
echo "output directory is ${output_directory}"
shift
ashs_type=$1
echo "ASHS type is ${ashs_type}"
shift
bids_output_file=$1
echo "symlink final output to bids named file ${bids_output_file}"
shift
options=$@

export ASHS_ROOT=$ashs_root
##Modules must unload/load in this order to prevent LIBTIFF version error
module unload matlab/2023a 
module load ImageMagick

### Make tmpdir to run ashs in
tmpdir=$( mktemp -d --tmpdir=/scratch )
# always remove tmpdir when script exits
trap "rm -rf $tmpdir" EXIT
echo $tmpdir

options="${options} -w ${tmpdir}"
echo $options

#run ASHS
$ASHS_ROOT/bin/ashs_main.sh $options

echo now copy files to $output_directory       
echo Here are the files in the tmpdir: 
ls -l $tmpdir
echo More extensive: 
tree $tmpdir

## Make ASHST1/ASHSICV/sfsegnibtend directory in session folder
if [[ ! -d $output_directory ]] ; then 
    mkdir -p $output_directory
fi

### Copy result files out of the tmp dir
## always copy log files
cp -r $tmpdir/dump $output_directory

### if success -- check for segmentation file we use for stats in /final
id=$( echo $options | tr ' ' '\n' | grep -e "-I" -A1 | sed 's/-I//' | tr -d '\n' ) 

if [[ -f "${tmpdir}/final/${id}_left_lfseg_heur.nii.gz" ]] ; then 
    echo "Found successful output, copying files to outputdir"

    ## symlink inputs: parse options arg for -f and -g values
    mprage_input=$( echo $options | tr ' ' '\n' | grep -e "-g" -A1 | sed 's/-g//' | tr -d '\n' ) # -g value
    tse_input=$( echo $options | tr ' ' '\n' | grep -e "-f" -A1 | sed 's/-f//' | tr -d '\n' ) # -f value
    ln -sv $mprage_input $output_directory/mprage.nii.gz
    ln -sv $tse_input $output_directory/tse.nii.gz

    ## for T1 ASHS
    if [[ $ashs_type == "T1ext" ]] ; then 
        mkdir -p $output_directory/affine_t1_to_template $output_directory/bootstrap/fusion/ $output_directory/final
        cp -v $tmpdir/affine_t1_to_template/*.mat $output_directory/affine_t1_to_template
        cp -v $tmpdir/bootstrap/fusion/posterior* $output_directory/bootstrap/fusion
        cp -v $tmpdir/final/${id}_[lr]* $output_directory/final
        ### all files in /final except icv.txt

        cp -rv $tmpdir/flirt_t2_to_t1 $tmpdir/qa $tmpdir/tse_native_chunk_* $output_directory
        
        ln -sv $output_directory/final/${id}_left_lfseg_heur.nii.gz $bids_output_file

    ## for T2 ASHS 
    elif [[ $ashs_type == "T2" ]] ; then
        mkdir -p $output_directory/affine_t1_to_template $output_directory/final
        cp -v $tmpdir/affine_t1_to_template/*.mat $output_directory/affine_t1_to_template
        cp -v $tmpdir/final/${id}_[lr]* $output_directory/final
        ### all files in /final except icv.txt

        cp -rv $tmpdir/bootstrap $tmpdir/flirt_t2_to_t1 $tmpdir/multiatlas $tmpdir/qa $output_directory
        
        ln -sv $output_directory/final/${id}_left_lfseg_corr_nogray.nii.gz $bids_output_file

    ## for ICV ASHS 
    elif [[ $ashs_type == "ICV" ]] ; then 
        cp -vr $tmpdir/final $tmpdir/qa $output_directory
        ln -sv $output_directory/final/${id}_left_lfseg_corr_nogray.nii.gz $bids_output_file
    fi 
else
    echo "final file not found"
fi 






# Options:
# for T1, T2, and ICV:
# -a atlas
# -w {self.filepath}/ASHST1 // /sfsegnibtend // /ASHSICV
# -g {self.t1trim}
# -f {self.superres}/{self.t2nifti}/{self.t1trim}
# -T
# -I {self.id}

# T1, ICV only:
# -m {long_scripts}/identity.mat  (Provide the .mat file for the transform between the T1w and T2w image.)
# -M (The mat file provided with -m is used as the final T2/T1 registration.
#                     ASHS will not attempt to run registration between T2 and T2.)

# ICV only: 
# -B (Do not perform the bootstrapping step, and use the output of the initial joint
#                     label fusion (in multiatlas directory) as the final output.)

# T1 extended/anterior atlas only: 
# -C ashs_config.sh  (variable for more slices in QC screenshots to cover ASHST1 extended atlas)

# ************UPDATE 7/4/2023 & 11/6/2023************
#     - removed -s 1-7 opt: unnecessary, default runs all 7 steps
#     - removed -d opt: debugging log unnecessary
#     - Modules must be in order: unload matlab, load ImageMagick to resolve LibTiff version error that prevents
#          creation of qa pngs. 
#     - removed -z {long_scripts}/ashs-fast-z.sh (Provide a path to an executable script that 
#           will be used to retrieve SGE, LSF, SLURM or GNU parallel opts for different stages of ASHS.)
#           -z ashs fast is deprecated in newer versions of ashs
#     - removed -l (Use LSF instead of SGE, SLURM or GNU parallel)
#           separating jobs prevents transer of module unload/load, leading to LibTiff version error still.
      
# ************UPDATE 10/7/2025************
#   -Instead of removing unneeded files, ASHS script outputs to tmp dir
#    and only necessary files are copied to final dataset directory.

# ************UPDATE 3/17/2026************
    # - added clause to use different ashs_config.sh file if using ASHST1 extended atlas for more slices and 
    # coverage in the QC png screenshots. 