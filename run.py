#!/usr/bin/bash

import argparse
import bids
from copy import deepcopy
from datetime import datetime
import json
import logging
import os
import pandas as pd
from pprint import pprint
from naccsc_configs import *
from wrap_submit_scripts import wrap_submit_superres, wrap_submit_T1ASHS


current_date = datetime.now().strftime("%Y%m%d")
current_date_time = datetime.now().strftime("%Y%m%dT%H%M%S")


# pass a filepath for an image
class bids_image():
    def __init__(self,filepath_to_image):
        self.file_hard_path = filepath_to_image
        self.subject = [x.split("-")[1] for x in self.file_hard_path.split("/") if "sub" in x][0]
        self.session = [x.split("-")[1] for x in self.file_hard_path.split("/") if "ses" in x][0]
        self.image_dir = os.path.dirname(self.file_hard_path)
        self.containing_bids_dir = self.file_hard_path.split("/sub-")[0] ## gets just the bids dir if raw, with derivative/name if derivative
        self.deriv_dir_name = self.containing_bids_dir.split("/")[-1]
        self.log_file = os.path.join(self.containing_bids_dir,"code","logs",self.deriv_dir_name, f"{self.deriv_dir_name}_{self.subject}_{self.session}_{current_date_time}_%J.txt")

    ## not part of init -- should only make dirs for a instance if actually running the code that will populate them
    def make_session_dirs(self):
        try:
            os.makedirs(self.image_dir)
        except FileExistsError as e:
            print(f"Directory {self.image_dir} already exists.")
        return 


def make_bids_dir(step):
    dir_to_make = os.path.join(bids_dir_filepath,"derivatives",processing_steps[step]['output_dir_name'])
    print(f"Making bids directory {dir_to_make}")
    if not os.path.exists(dir_to_make):
        os.makedirs(f"{dir_to_make}/code/logs/{processing_steps[step]['output_dir_name']}")
        if not os.path.exists(f"{dir_to_make}/dataset_description.json"):
            make_dataset_descript_json(dir_to_make,step)
    else:
        print("directory already exists")
    return 


def make_dataset_descript_json(dirpath,step):
    print('you have to make a dataset description json for the directory')
    ### TODO: how to write json file info. need script information from processing_steps, date? 
    return


## use pybids library to get filepaths for existing bids files and create bids_image objects
def get_images(data_dir_filepath, filters, validate_bids=False):
    ## pass filepath to derivative directory with validate=False 
    layout = bids.BIDSLayout(data_dir_filepath, validate = validate_bids)
    allimages = layout.get(return_type = "filename", extension = ["nii.gz", "nii"], **filters, invalid_filters="allow", regex_search = True)
    # print(allimages)
    ## TODO: decide behavior when no images found -- raise error here or is empty list ok?
    bidsimage_objects = []
    for image in allimages:
        bidsimage_objects.append(bids_image(image))
    return bidsimage_objects


## use pybids library to get filepaths for bids files that don't yet exist and create bids_image objects
def build_bids_filepath(outputdir, this_step_filters_output):
    pattern = "sub-{subject}[_ses-{session}][_desc-{description}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_desc-{desc}]_{suffix}.nii.gz",
    layout = bids.BIDSLayout(outputdir, validate=False)
    output_file = bids_image(layout.build_path(this_step_filters_output, pattern, validate=False))
    return output_file


### -w argument has to be in double quotes
def set_submit_options(this_job_name, output_dir, parent_job_name):
    jobname = f"-J {this_job_name}"
    output = f"-o {output_dir}/{this_job_name}_{current_date_time}.txt"
    if parent_job_name:
        if len(parent_job_name) == 2: 
            wait = f'-w "done({parent_job_name[0]}) && done({parent_job_name[1]})"'
        elif "stats" in this_job_name:  
            wait = f'-w "ended({parent_job_name[0]})"'
        else:
            wait = f'-w "done({parent_job_name[0]})"'
    else:   
        wait = ""
    return f"{jobname} {output} {wait}"


def submit_process_jobs(sub,ses,steptodo):  
    '''sets up common bids attributes before calling specific processing script with any particulars'''
    
    ##### Get input file(s)
    this_step_filters_input = {**processing_steps[steptodo]['input_filters'], **{"session":f"{ses}", "subject":f"{sub}"}}
    print(f"Using filters: {this_step_filters_input} to find images")
    input_files = get_images(os.path.join(bids_dir_filepath,processing_steps[steptodo]['input_dir_filepath']), this_step_filters_input)
    ## TODO: make step_to_do a class populated from config? could access folders more easily??

    ## NOTE: regex on acquisition still returning both values instead of only 1, might be fixable, tempfilter post-get_images function added
    ## hard-coded filter for now while pybids returning all possible option non-preferentially 
    ## also updates filter variable for future use based on which acq found
    eight_check = [i for i in input_files if "800um" in i.file_hard_path]
    if len(eight_check) > 0:
        print('800um found, drop others')
        input_files = eight_check
        this_step_filters_input['acquisition'] = "800um"
    else:
        mprage_check = [i for i in input_files if "MPRAGE" in i.file_hard_path]
        if len(mprage_check) > 0: 
            print("No 800um but found MPRAGE instead, use that one")
            input_files = mprage_check
            this_step_filters_input['acquisition'] = "MPRAGE1mm"

        else:
            print(f"No 800um or MPRAGE acquisitions found for {this_step_filters_input}.")
            return
 
    # Run processing for each image found
    for i in input_files:
        print(f"use this input file: {i.file_hard_path}") 

        ## set up output directory path and output filters
        outputdir=os.path.join(bids_dir_filepath,"derivatives",processing_steps[steptodo]['output_dir_name'])
        ### Adjust filters for output file (keep any values from input filters if not changed in output_files for step)
        this_step_filters_output = deepcopy(this_step_filters_input)
        for key,value in processing_steps[steptodo]['output_filters'].items(): 
            if key in this_step_filters_output:
                print(f'updating {key} to {value} find output file')
                this_step_filters_output[key] = value
        
        ### Quick check for output file
        if output_check == True:
            output_files = get_images(outputdir,this_step_filters_output)
            for o in output_files: 
                # print(o.file_hard_path)
                if os.path.isfile(o.file_hard_path):
                    print(f"Output file {o.file_hard_path} already exists, not submitting the job.")
                    ## TODO: break/error of some kind -- only for this input file, so not a full return. continue? need to not be in a for loop of output files
                    ## TODO: also handle the list aspect -- list comprehension with boolean check?
                    return ## return for now, won't work in implementation b/c of run possibilities 
        
        ## get filepath for output file 
        output_file = build_bids_filepath(outputdir, this_step_filters_output)
        # print(output_file.file_hard_path)
        output_file.make_session_dirs() 

        ## set up bsub options 
        submit_options = f"-o {self.logfile}"
        ### TODO: -J job names for tracking connected jobs
        ### TODO: bsub options function to add -w code tracking? 
            # submit_options = set_submit_options(this job name, log dir, output_job_name)  
            ## parent job info -- not sure how that will be tracked yet
            ##

        ## TODO: how to set up run scripts as variables linked to each step: 
            ##e.g. processing_steps[steptodo]['run_script'] = bids_superres.sh, run scripts in the same folder as this script, os.path.join(this_script_dir,variable)
            ## hard-code if/else
            # python modules imported -- no, can't call a function by having the value from a variable be the function name (I think)
        ## TODO: handling lists of inputs/outputs 
        if steptodo == "superres":
            wrap_submit_superres(i, output_file, submit_options)
            # process_script_path = os.path.join(os.path.dirname(__file__),processing_steps[steptodo]['processing_script'])
            # print(f"bsub {submit_options} bash {process_script_path} {i.file_hard_path} {output_file.file_hard_path}")
        elif steptodo == "t1ext_ashs":
            wrap_submit_T1ASHS(i, output_file, submit_options)

    return 


if __name__ == "__main__":

    ## two ways to do processing:
        ## 1. run all sub/ses listed in csv
        ## 2. check all sub/ses in csv, get a list of which need to be done, submit only the todo sessionss for processing 

    ## TODO: use positional arguments for required inputs (seems like the best practice way to do that)

    parser = argparse.ArgumentParser()
    # parser.add_argument("-c", "--csv", help = "Csv of sub,ses without header.", required = True)
    parser.add_argument("-d", "--dry_run", action = "store_true", help = "Dry run this script without submitting any processing jobs.")
    # parser.add_argument("-t", "--select_todo_sessions", action = "store_true", help = "Check all sessions in the csv for any that need to be run and only submit jobs for those sessions instead of all sessions in csv.")
    # parser.add_argument("-f", "--filter_bids", help = "JSON file with bids filters only for acq- entity or other entities used to differentiate between images with the same suffix.")
    parser.add_argument("-s", "--stepstodo", help = "", choices = list(processing_steps.keys()), nargs = "+") ##TODO: fix formatting on choices, printing as dict then list with dict in help function
    parser.add_argument("-u", "--check_for_output", choices = ["skip_check", "check_first"], help = "Set behavior for checking for existing output. Skip the check or check before submitting a job. Default is to check first.", default = "check_first")
    
    ## always need to submit a csv (SUB, SES)
         ## not any versions with mridate and petdate as input -- have that match determined within registration scripts
    ## use csv as-is or parse for to-dos: store True to run function for parsing for to-dos (required to chose one or the other)
    
    ## TODO: for selecting to-do sessions, can also give directory path and check for completion?
    ## TODO: which steps to do: chose from list: t1, t2, flair,diffusion,pet-mri reg*
        ##  can give more granular step options (optional) for each sequence type processing
    ## TODO: config file with filepaths
    ## TODO: add option to overwrite existing output 

    ##TODO: function to match MRI to PET dates for registration 

    ##TODO: separate script/function parse /bids folder for complete session lists -- 
        ## similar to /project/wolk_4/naccsc_bids/scripts/dcm2bids_scripts/tabulate_dcm2bids_helper.py 
        ## that can run on ADNI data as well, not wrapped inside of dcm2bids tmp dirs
    
    args = parser.parse_args()

    ## Set up bids directories & dataset_description.json for each step
    if not args.dry_run:
        for step in args.stepstodo: 
            make_bids_dir(step)
    
    ## Set whether or not to check for output first (can skip if you know nothing exists)
    if args.check_for_output == "skip_check":
        output_check = False
    else:
        output_check = True

    csv="/project/wolk_4/naccsc_bids/lists/sm_testlist.csv"
    ## TODO: faster way to read csv than pandas df? 
        ## try engine="pyarrow", need to get pyarrow installed first though
        ## reading the csv is a trivial gain if switching to parallel session processing, not a priority
    df=pd.read_csv(csv, header=None, names = ['ID','SESSIONNAME'])

    for index,row in df.iterrows():
        sub = row['ID']
        ses = row['SESSIONNAME']    
        ## TODO: spin off each sub/ses to go through the process parallelly instead of sequentially?
            # one master job for each sub,ses  to run -- all steps to do coordinated through that job
        print()
        print(f"Starting processing for subject {sub} session {ses}")

        for steptodo in args.stepstodo: 
            # TODO: t1preproc/ants require whole csv list, config script -- handle that setup differently?
            submit_process_jobs(sub,ses,steptodo)
        
        break

    # test = bids_image("/project/wolk_4/naccsc_bids/bids/sub-132132/ses-132132x20250407x3TxABCD2/anat/sub-132132_ses-132132x20250407x3TxABCD2_acq-800um_T1w.nii.gz")
    # test = bids_image("/project/wolk_4/naccsc_bids/bids/derivatives/superres/sub-131378/ses-131378x20250410x3TxABCD2/anat/sub-131378_ses-131378x20250410x3TxABCD2_acq-800um_desc-superres_T1w.nii.gz")
    # print(test.containing_bids_dir)
    # print(test.log_file)
