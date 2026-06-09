#!/usr/bin/env python3

#### Stuff to change/fill out for each dataset
bids_dir_filepath = "/project/wolk_4/naccsc_bids/bids"
## python environment:
## conda activate /project/wolk_4/emcgrew/picslbids

## optional bids filters: anything to filter on other than subject, session, datatype, suffix
custom_t1w_filters = [
    {"acquisition":"800um"},
    {"acquisition":"MPRAGE1mm"}
]

custom_t2w_filters = [
    {"acquisition":"400um"}
]

custom_flair_filters = [
    {"acquisition":"accSag"}
]

## Add to subject and session filters in run.py to do most basic filter of all files with that suffix
basic_t1w_filters = {"datatype":"anat", "suffix":"T1w"} 
basic_t2w_filters = {"datatype":"anat", "suffix":"T2w"} 
basic_flair_filters = {"datatype":"anat", "suffix":"FLAIR"} 

## New steps:
# t1w_preproc 
    # cross ANTs   
        # longANTs
            # parcellation 
                # inf_cereb_mask
                # structure stats from ANTs 
                # pmtau (?)
    # t1icv
    # superres
        # t1ext_ashs
            # crashs
            # T1 ASHS & CRASHS stats
    # t2ashs
        # prc_cleanup
            # t2 ashs stats
    # t1_pet_reg
        # t1_pet_suvr
            # pet_reg_qc
                # pet-mri stats
# flair_skull_strip 
    # wmh_seg
        # wmh stats

## for each processing step, define bids filter, dirname, processing script? in a dict 
## use 'filters' keyword to store additional filter objects other than sub, ses, acq, suffix, datatype that are set in basic and custom filters
processing_steps = {
    "T1w_preproc":
    {
        "input_step":None, "output_dir_name":"T1wPreprocessing_061"
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
        "input_step":"T1w_preproc", "input_filters":{"desc": "preproc"}, "processing_script": "", "output_dir_name": "superres", "output_filters":{"desc": "superres"}
    },
    "t1ext_ashs": 
    {
        "input_step":"superres", "input_filters":{"desc": "preproc"}, "processing_script": "", "output_dir_name":"ASHST1", "output_filters":{"atlas": "ASHST1ant", "desc": "lfsegheur"}
    },
    "crashs": 
    {
        "input_step":"t1ext_ashs", "output_dir_name":"ASHST1"
    }
}

