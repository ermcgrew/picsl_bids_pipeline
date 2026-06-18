#!/usr/bin/env python3

## each processing script as a function/module that could be imported/called
## these functions contain any of the specific-to-each-step inputs/outputs and call the bash scripts that do the processing 
## all receive same parameters: input, output, bsub_options

import json
import os
import subprocess 
## have all imports & other standard stuff in configs, then import configs into all files? 


## TODO: other info for json files?
def make_output_json_file(json_filepath, input_bids_uri, script_loc):
    # print('making ouptut json file')
    json_info = {
        "Sources" : [
            input_bids_uri
        ]
    }

    with open(json_filepath, "w") as file:
        json.dump(json_info, file, indent=4)
    return


def wrap_submit_superres(input, output, bsub_options):
    print('this is the superres function in test.py')

    script_filepath=os.path.join(os.path.dirname(__file__),"superres_just_bash_parts.sh")
    print(f"bsub {bsub_options} bash {script_filepath} {input.file_hard_path} {output.file_hard_path}")

    json_filepath = output.json_file
    make_output_json_file(json_filepath, input.bids_uri, script_filepath)
        ## but I really need the SRPATH value that's coded in the script itself now...

    return 


def wrap_submit_T1ASHS(input, output, bsub_options):
    print("this is the wrap submit T1ashs function")
    ## uses superres nifti as input needed (b/c t1trim will exist because it's the input for superres)

    ## store these filepaths here, or in a config file? Will they change with ASHS update to bids?
    ashs_t1ext_atlas="/project/bsc/shared/AshsAtlases/ashs_atlas_upennpmc_t1ext_20240617/final/"
    ashs_mopt_mat_file=""
    t1extashs_qc_slice_config=""

    superres_nifti = input.file_hard_path
    t1trim_nifti = "" ## TODO: derive from superres how?

    output_dir=output.image_dir
    id_opt=output.subject
    # print(f"bsub {bsub_options} bash {os.path.join(os.path.dirname(__file__),'ashs.sh')}")

    ## could call directly from here without doing more set up in a bash script?
    ## all ashs calls would be separate instead of running from one script (that's ok)

    ## get tmpdir function here 
    ashs_tmpdir=""
    options=f"-a {ashs_t1ext_atlas} -g {t1trim_nifti} -f {superres_nifti} \
          -w {ashs_tmpdir} -T -d -I {id_opt} -m {ashs_mopt_mat_file} -M -C {t1extashs_qc_slice_config}"
    ## set ASHS_ROOT for system -- subprocess(export ASHSROOT)
    # print(f"bsub {bsub_options} bash {ASHS_ROOT}/bin/ashs_main.sh {options}")

    ## clean up tmpdir -- function shared with other ashs calls?

    # make_output_json_file()

    return


def wrap_submit_T2_ASHS():
    print("this is the t2 ashs function in test.py")
    
    #ashs inputs if keeping the same ashs run script
    # t1trim=$3 --passed as input #1
    # t2link=$4 --pased as input #2
    # output_directory=$5 -- passed in
    # id=$6 -- derive from input


    ## static from config
    # ashs_root=$1
    # atlas=$2
    # m_opt=$7


    return
