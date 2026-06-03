#!/usr/bin/env python3

## python environment:
## conda activate /project/wolk_4/emcgrew/picslbids


## Add to subject and session filters in run.py to do most basic filter of all files with that suffix
basic_t1w_filters = {"datatype":"anat", "suffix":"T1w"} 
basic_t2w_filters = {"datatype":"anat", "suffix":"T2w"} 
basic_flair_filters = {"datatype":"anat", "suffix":"FLAIR"} 




#### Stuff to change/fill out for each dataset
bids_dir_filepath = "/project/wolk_4/naccsc_bids/bids"

## optional bids filters: anything to filter on other than subject, session, datatype, suffix
custom_t1w_filters = [
    {"acquisition":"800umxND"},
    {"acquisition":"MPRAGE1mm"}
]

custom_t2w_filters = [
    {"acquisition":"400um"}
]

custom_flair_filters = [
    {"acquisition":"accSag"}
]





## New steps, with match to previous: (just the t1 steps for now)
# t1w_preproc == neck_trim 
# cross ANTs == cortical_thick, brain_ex  
# longANTs
# parcellation == whole_brain_seg, wbsegqc
    # no wbseg_to_ants needed anymore
# inf_cereb_mask (?)
# pmtau (?)
# t1icv
# superres
# t1ext_ashs
# crashs == t1mtthk
# T1 ASHS & CRASHS stats
# structure stats from ANTs 

# t2 steps: 
# t2ashs
# still need to do prc_cleanup?
# t2 ashs stats

#flair:
# flair_skull_strip 
# wmh_seg
# wmh stats

# pet:
# t1_pet_reg
# t1_pet_suvr
# pet_reg_qc
# pet-mri stats

## for each processing step you're going to do, define the following in a dict? 
## bids filter, dirname, processing script?
## use 'filters' keyword to store additional filter objects other than sub, ses, acq, suffix, datatype that are set in basic and custom filters
processing_steps = {
    "T1w_preproc":
    {
        "filters":{}, "dirname":"T1wPreprocessing_061"
    },
    # "xANTs": 
    # {
    #     "filters":{}, "dirname":""
    # },
    # "longANTs": 
    # {
    #     "filters":{}, "dirname":""
    # },
    # "parcANTs": 
    # {
    #     "filters":{}, "dirname":""
    # },
    # "t1icv": 
    # {
    #     "filters":{}, "dirname":"ASHST1"
    # },
    # "superres": ## run_pipeline version
    # {
    #     "filters":{"desc": "superres"}, "dirname":"ASHST1", "input_step":"T1w_preproc"
    # },
     "superres": 
    {
        "input_step":"T1w_preproc", "input_filters":{"desc": "preproc"}, "output_dir_name": "superres", "output_filters":{"desc": "superres"}
    },
    "t1ext_ashs": 
    {
        "filters":{"atlas": "ASHST1ant", "desc": "lfsegheur"}, "dirname":"ASHST1", "input_step": "superres"
    },
    # "crashs": 
    # {
    #     "filters":{}, "dirname":"ASHST1"
    # }
}

