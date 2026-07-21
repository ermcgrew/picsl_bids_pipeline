#!/usr/bin/env python3

import argparse
import bids
from bids.layout import parse_file_entities
from copy import deepcopy
from datetime import datetime
import json
import logging
import os
import pandas as pd
import subprocess 

current_date = datetime.now().strftime("%Y%m%d")
current_date_time = datetime.now().strftime("%Y%m%dT%H%M%S")

logging.basicConfig(level=logging.INFO)

#### filepaths, filters to fill out for each dataset
## Top level bids directory
bids_dir_filepath = "/project/wolk_4/naccsc_bids/bids"
## python environment:
## conda activate /project/wolk_4/emcgrew/picslbids


##ASHS processing cluster filepaths
ashs_root = "/project/hippogang_2/pauly/wolk/ashs-fast"
icv_atlas = "/project/bsc/shared/AshsAtlases/ashs_atlas_icv/final"
ashs_t2_atlas = "/project/bsc/shared/AshsAtlases/ashs_atlas_upennpmc_20170810"
ashs_t1ext_atlas = "/project/bsc/shared/AshsAtlases/ashs_atlas_upennpmc_t1ext_20240617/final/" 
ashs_mopt_mat_file = "/project/wolk/ADNI2018/scripts/adni_processing_pipeline/utilities/identity.mat"
t1extashs_qc_slice_config="/project/wolk/ADNI2018/scripts/adni_processing_pipeline/utilities/ashs_config.sh"


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
        "acquisition":"accSag"
    }  
}


## for each processing step, bids filter, dirname, processing scripts in a dict 

## any changes to the inputs/outputs to each processing step can be made in the filters keyword
## any bids entity's values that change between input and output of a step should be noted in the output_filter keyword dictionary
## e.g. the value of "desc" for the superres step is "preproc" for input, and "superres" for output
## Users can edit the filters to select different files to run through each step
## (e.g. If you wanted to run superres step on original un-trimmed T1w scan, remove "desc: preproc" from superres['input_filters'])

## this is files, actually, not steps
proc_steps = {
    "t1":
    {
        "input_files": [
            None
        ],
        "directory":"",
        "filters": {**basic_bids_filters['t1w']}
    },
    "t2":
    {
        "input_files": [
            None
        ],
        "directory":"",
        "filters": {**basic_bids_filters['t2w']}
    },
    "flair":
    {
        "input_files": [
            None
        ],
        "directory":"",
        "filters": {**basic_bids_filters['flair']}
    },
    "t1w_preproc":
    {
        "input_files": [
            None
        ],
        "directory":"derivatives/T1wPreprocessing_061",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "preproc"}}
    },
    "inf_cereb_mask":
    {
        "input_files": [
            "@@"
        ],
        "directory":"derivatives/@@",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "@@"}}
    },
    "ants_stats":{
        "input_files": [
            "@@"
        ],
        "directory":"derivatives/@@",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "ants_stats"}}
    },
    "pmtau":{
        "input_files": [
            "@@"
        ],
        "directory":"derivatives/@@",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "@@"}}
    },
     "t1icv": 
    {
        "input_files": [
            "t1w_preproc"
        ],
        "directory":"derivatives/ASHSICV",
        "filters": {**basic_bids_filters['t1w'], **{"atlas": "ASHSICV", "desc": "lfsegcorrnogray"}}
    },
    "superres":
    {
        "input_files": [
            "t1w_preproc"
        ],
        "directory":"derivatives/superres",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "superres"}}
    }, 
    "t1ext_ashs":
    {
        "input_files": [
            "t1w_preproc", "superres" ## gopt t1image first, fopt t2image second
        ],
        "directory":"derivatives/ASHST1",
        "filters": {**basic_bids_filters['t1w'], **{"atlas": "ASHST1ant", "desc": "lfsegheur"}}
    },
    "crashs":
    {
        "input_files": [
            "t1ext_ashs"
        ],
        "directory":"derivatives/CRASHS",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "@@"}}
    }, 
    "t1ashs_stats":{
        "input_files": [
            "crashs"
        ],
        "directory":"derivatives/t1ashs_stats",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "t1ASHS_stats"}}
    },
    "t2ashs":
    {
        "input_files": [
            "t1w_preproc", "t2" ## gopt t1image first, fopt t2image second
        ],
        "directory":"derivatives/ASHST2",
        "filters": {**basic_bids_filters['t2w'], **{"atlas":"ASHST2", "desc": "lfsegcorrnogray"}}
    }, 
    "prc_cleanup":
    {
        "input_files": [
            "t2ashs"
        ],
        "directory":"derivatives/prc_cleanup",
        "filters": {**basic_bids_filters['t2w'], **{"atlas":"ASHST2", "desc": "prccleanup"}}
    },
    "t2ashs_stats":{
        "input_files": [
            "prc_cleanup"
        ],
        "directory":"derivatives/t2ashs_stats",
        "filters": {**basic_bids_filters['t2w'], **{"desc": "t2ashs_stats"}}
    },
    "flair_skull_strip":{
        "input_files": [
            "flair"
        ],
        "directory":"derivatives/flair_skull_stripped",
        "filters": {**basic_bids_filters['flair'], **{"desc": "skullstrip"}}
    },
    "wmh_seg":{
        "input_files": [
            "flair_skull_strip"
        ],
        "directory":"derivatives/flair_wmh_seg",
        "filters": {**basic_bids_filters['flair'], **{"seg": "wmh"}}
    },
     "wmh_stats":{
        "input_files": [
            "wmh_seg"
        ],
        "directory":"derivatives/wmh_stats",
        "filters": {**basic_bids_filters['flair'], **{"desc": "flair_stats"}}
    },     
    "t1_pet_reg":{
        "input_files": [
            "@@"
        ],
        "directory":"derivatives/@@",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "@@"}}
    },        
    "t1_pet_suvr":{
        "input_files": [
            "@@"
        ],
        "directory":"derivatives/@@",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "@@"}}
    },        
    "pet_reg_qc":{
        "input_files": [
            "@@"
        ],
        "directory":"derivatives/@@",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "@@"}}
    },
    "pet_reg_stats":{
        "input_files": [
            "@@"
        ],
        "directory":"derivatives/@@",
        "filters": {**basic_bids_filters['t1w'], **{"desc": "@@"}}
    },
}
