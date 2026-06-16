#!/usr/bin/env python3

## each processing script as a function/module that could be imported/called
## these functions contain any of the specific-to-each-step inputs/outputs and call the bash scripts that do the processing 
## all receive same parameters: input, output, bsub_options

import os
import subprocess 
## have all imports & other standard stuff in configs, then import configs into all files? 


## TODO: write this function
def make_output_json_file():
    print('making ouptut json file')
    return


def wrap_submit_superres(inputs, outputs, bsub_options):
    print('this is the superres function in test.py')
    # print(inputs)
    # print(outputs)
    # print(bsub_options)

    print(f"bsub {bsub_options} bash {os.path.join(os.path.dirname(__file__),"superres_just_bash_parts.sh")} \
    {inputs.file_hard_path} {outputs.file_hard_path}")

    make_output_json_file()

    return 


def wrap_submit_T1ASHS(inputs, outputs, bsub_options):
    print("this is the wrap submit T1ashs function")

    print(f"bsub {bsub_options} bash {os.path.join(os.path.dirname(__file__),'run_ashs.sh')} \
    {ashs_root} {ashs_t1ext_atlas} {self.t1trim} {self.superres_nifti}\
        {self.t1ashsext_dir} {self.id} {ashs_mopt_mat_file}")
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
