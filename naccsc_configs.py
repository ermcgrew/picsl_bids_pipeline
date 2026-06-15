#!/usr/bin/env python3

#### filepaths, filters to fill out for each dataset

## Top level bids directory
bids_dir_filepath = "/project/wolk_4/naccsc_bids/bids"
## python environment:
## conda activate /project/wolk_4/emcgrew/picslbids

### filters to use for all steps performed on each type of image
basic_bids_filters = {
    "t1w": {
        "datatype":"anat",
        "suffix":"T1w",
        "acquisition":"800um$|MPRAGE1mm"
    },
    "t2w":{
        "datatype":"anat",
        "suffix":"T2w",
        "acquisition":"400um"
    },
    "flair":{
        "datatype":"anat",
        "suffix":"FLAIR",
        "acquisition":"SagFLAIR"
    }  
}


## for each processing step, bids filter, dirname, processing scripts in a dict 

## any changes to the inputs/outputs to each processing step can be made in the filters keyword
## any bids entity's values that change between input and output of a step should be noted in the output_filter keyword dictionary
## e.g. the value of "desc" for the superres step is "preproc" for input, and "superres" for output
## Users can edit the filters to select different files to run through each step
## (e.g. If you wanted to run superres step on original un-trimmed T1w scan, remove "desc: preproc" from superres['input_filters'])

processing_steps = {
    "T1w_preproc":
    {
        "input_step": None, 
        "input_dir_filepath":"",
        "input_filters":{
            **basic_bids_filters['t1w']
        },
        "processing_script": "", 
        "output_dir_name": "T1wPreprocessing_061", 
        "output_filters": 
            {
                "desc": "preproc"
            },
        "suffix": "t1w"
    },
    "xANTs": 
    {
        "input_step":"T1w_preproc", "output_dir_name":""
    },
    "longANTs": 
    {
        "input_step":"xANTs", "output_dir_name":""
    },
    "parcANTs": 
    {
        "input_step":"longANTs", "output_dir_name":""
    },
    "t1icv": 
    {
        "input_step":"T1w_preproc", "output_dir_name":"ASHSICV"
    },
     "superres": 
    {
        "input_step":"T1w_preproc", 
        "input_dir_filepath":"derivatives/T1wPreprocessing_061",
        "input_filters":{**basic_bids_filters['t1w'], **{"desc": "preproc"}}, 
        "processing_script": "superres_just_bash_parts.sh", 
        "output_dir_name": "superres", 
        "output_filters": {"desc": "superres"},
        "suffix": "t1w"
    },
    "t1ext_ashs": 
    {
        "input_step":"superres", 
        "input_dir_filepath":"derivatives/superres",
        "input_filters":{**basic_bids_filters['t1w'], **{"desc": "superres"}}, 
        "processing_script": "", 
        "output_dir_name":"ASHST1", 
        "output_filters":{"atlas": "ASHST1ant", "desc": "lfsegheur"},
        "suffix": "t1w"
    },
    "crashs": 
    {
        "input_step":"t1ext_ashs", "output_dir_name":"CRASHS"
    }
}

