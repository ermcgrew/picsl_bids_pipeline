#!/usr/bin/env python3

## can't think of a better name than test right now
## what if each processing script was a function that could be called in run.py from here
## these functions contain any of the specific-to-each-step inputs/outputs and call the bash scripts that do the processing 
## all receive inputs of input file name, output file dir?
import subprocess 

def superres():
    print('this is the superres function in test.py')
    print("/project/wolk_4/naccsc_bids/scripts/picsl_bids_pipeline/superres_just_bash_parts.sh $input $output")

    return 


def T2_ASHS():
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
