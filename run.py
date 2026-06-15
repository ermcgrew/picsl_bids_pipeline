#!/usr/bin/bash

import argparse
import bids
from copy import deepcopy
import json
import os
import pandas as pd
from pprint import pprint
from naccsc_configs import *
from test import superres

# bids.config.set_option('extension_initial_dot', True)


# don't do layout.get in class, pass the filepath for the image to the class
class bids_image():
    def __init__(self,filepath_to_image):
        self.file_hard_path = filepath_to_image
        self.subject = [x.split("-")[1] for x in self.file_hard_path.split("/") if "sub" in x][0]
        self.session = [x.split("-")[1] for x in self.file_hard_path.split("/") if "ses" in x][0]
        self.image_dir = os.path.dirname(self.file_hard_path)
        self.containing_bids_dir = self.file_hard_path.split("/sub-")[0] ## gets just the bids dir if raw, with derivative/name if derivative
        self.dataset_descrip_file = os.path.join(self.containing_bids_dir,"dataset_description.json")


    # def get_deriv_file(self, deriv_dir_name, **filters):
    #     ## deriv file is not an attribute of the class, it's another instance of the class 
    #         ## allows for multiple deriv files to be determined for each file
    #         ## handling of multiple deriv matches -- not sure if allowing only 1 is the best move
    #     layout = bids.BIDSLayout(bids_dir_filepath, derivatives=True)
    #     self.get_data_description(deriv_dir_name) ## read dataset_description.json for pipeline name to pass to layout.get scope arg
    #     print(filters)
    #     print(self.pipeline_desc_name)
    #     ## subject and session already in filters subject=self.subject, session = self.session, 
    #     bids_matches = layout.get(extension='nii.gz', return_type="filename", **filters, scope=self.pipeline_desc_name)
    #     print(bids_matches)
    #     if len(bids_matches) == 1:
    #         return bids_image(bids_matches[0])
    #     elif len(bids_matches) > 1:
    #         print(f"More than one match using filters {filters}, only one match allowed")
    #         return False
    #     else:
    #         return False
    

    # def get_data_description(self, deriv_dir_name = ""):
    #     if deriv_dir_name:
    #         filepath_to_join = f"{bids_dir_filepath}/derivatives/{deriv_dir_name}"
    #     else:
    #         filepath_to_join = bids_dir_filepath

    #     try: 
    #         with open(os.path.join(filepath_to_join, "dataset_description.json"), 'r') as file:
    #             data_descript = json.load(file)
    #         # self.pipeline_desc_name = data_descript['PipelineDescription']['Name']
    #         self.pipeline_desc_name = data_descript['GeneratedBy'][0]['Name']
    #     except FileNotFoundError:
    #         print("a dataset description.json file must exist for the derivative pipeline output.")
    #         self.pipeline_desc_name = "" #set to empty so class doesn't error out when trying to use self.pipeline_desc_name
    #         ## will error out if no 'outputs exist yet, which is fine, because then the output files are definitely missing and the deriv pipeline needs to be run.

    ## TODO: have this run as part of init of class object instead of calling within script -- no? 
        ## should only make dirs for a instance if actually running the code that will populate them
    def make_session_dirs(self):
        print(f"Making directory for session")
        if not os.path.exists(self.containing_bids_dir): 
            make_bids_dir(self.containing_bids_dir)
        
        os.makedirs(self.image_dir)
        return 




def make_bids_dir(dir_to_make):
    print(f"Making bids directory {dir_to_make}")
    if not os.path.exists(dir_to_make):
        os.makedirs(f"{dir_to_make}/code/logs")
        if not os.path.exists(f"{dir_to_make}/dataset_description.json"):
            make_dataset_descript_json(dir_to_make)
    else:
        print("directory already exists")
    return 


def make_dataset_descript_json(dirpath):
    print('you have to make a dataset description json for the directory')
    return


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


def submit_process_jobs(sub,ses,steptodo):  
    '''sets up common bids attributes before calling specific processing script with any particulars'''
    
    ##### Get input file(s)
    this_step_filters_input = {**processing_steps[steptodo]['input_filters'], **{"session":f"{ses}", "subject":f"{sub}"}}
    print(f"Using filters: {this_step_filters_input} to find images")
    input_files = get_images(processing_steps[steptodo]['input_dir_filepath'], this_step_filters_input)
    ## TODO: how to set filepath from config? use the keyword 'input_step' to get that step output dir from processing steps dict? 
    ## make step_to_do a class populated from config? could access folders more easily??

    ## NOTE: regex on acquisition still returning both values instead of only 1, might be fixable, tempfilter post-get_images function added
    ## hard-coded filter for now while pybids returning all possible option non-preferentially 
    eight_check = [i for i in input_files if "800um" in i.file_hard_path]
    if len(eight_check) > 0:
        print('800um found, drop others')
        input_files = eight_check
    else:
        mprage_check = [i for i in input_files if "MPRAGE" in i.file_hard_path]
        if len(mprage_check) > 0: 
            print("No 800um but found MPRAGE instead, use that one")
            input_files = mprage_check
        else:
            print("Not using 800um or MPRAGE acquisitions.")
 
    # Run processing for each image found
    for i in input_files:
        print(f"use this input file: {i.file_hard_path}") 


        ### Quick check for output file
        outputdir=os.path.join(bids_dir_filepath,"derivatives",processing_steps[steptodo]['output_dir_name'])
        ### Adjust filters for output file (keep any values from input filters if not changed in output_files for step)
        this_step_filters_output = deepcopy(this_step_filters_input)
        for key,value in processing_steps[steptodo]['output_filters'].items(): 
            if key in this_step_filters_output:
                print(f'updating {key} to {value} find output file')
                this_step_filters_output[key] = value

        output_files = get_images(outputdir,this_step_filters_output)
        for o in output_files: 
            print(o.file_hard_path)
            if os.path.isfile(o.file_hard_path):
                print(f"Output file {o.file_hard_path} already exists, not submitting the job.")
                ## TODO: break/error of some kind -- only for this input file, so not a full return. continue? need to not be in a for o in output files
                ## TODO: also handle the list aspect -- list comprehension with boolean check?
                return ## return for now, won't work in implementation b/c of run possibilities 
    
        print("do the rest of the set up for output")
        ## remaining set up for running step: 
        # make session output dir (this also checks the overall bids dir exists)
        # output_file.make_session_dirs() 

        ##### set up json output for each output file
        # make_dataset_descript_json(self.containing_bids_dir)

        ## also set up bsub options here? always needed by submit scripts, but could call from submit scripts module? depends what info needed
        ## parent job info -- not sure how that will be tracked yet
        ## TODO: bsub options functions

        ## TODO: code run scripts as variables linked to each step: e.g. processing_steps[steptodo]['run_script'] = bids_superres.sh
            ## or just hard-code if/else? Separate scripts, or python modules imported?
        ## run scripts in the same folder as this script, os.path.join(this_script_dir,variable)
        # os.system(f"bsub -o /project/wolk_4/naccsc_bids/bids/derivatives/superres/code/logs/%J.txt bash bids_superres.sh {i.file_hard_path} {output_dir}")
        # superres()

    return 


if __name__ == "__main__":

    ## two ways to do processing:
        ## 1. run all sub/ses listed in csv
        ## 2. check all sub/ses in csv, get a list of which need to be done, submit only the todo sessionss for processing 

    ## TODO: use positional arguments for required inputs (seems like the best practice way to do that)

    parser = argparse.ArgumentParser()
    # parser.add_argument("-c", "--csv", help = "Csv of sub,ses without header.", required = True)
    # parser.add_argument("-d", "--dry_run", action = "store_true", help = "Dry run this script without submitting any processing jobs.")
    # parser.add_argument("-s", "--select_todo_sessions", action = "store_true", help = "Check all sessions in the csv for any that need to be run and only submit jobs for those sessions instead of all sessions in csv.")
    # parser.add_argument("-f", "--filter_bids", help = "JSON file with bids filters only for acq- entity or other entities used to differentiate between images with the same suffix.")
    ## always need to submit a csv (SUB, SES)
         ## not any versions with mridate and petdate as input -- have that match determined within registration scripts
    ## use csv as-is or parse for to-dos: store True to run function for parsing for to-dos (required to chose one or the other)
    
    ## TODO: for selecting to-do sessions, can also give directory path and check for completion?
    ## TODO: which steps to do: chose from list: t1, t2, flair,diffusion,pet-mri reg*
        ##  can give more granular step options (optional) for each sequence type processing
    ## dry run option -- don't submit anything 
    ## TODO: config file with filepaths
    ## TODO: add option to overwrite existing output 
    ##TODO: function to match MRI to PET dates for registration 

    ##TODO: separate script/function parse /bids folder for complete session lists -- 
        ## similar to /project/wolk_4/naccsc_bids/scripts/dcm2bids_scripts/tabulate_dcm2bids_helper.py 
        ## that can run on ADNI data as well, not wrapped inside of dcm2bids tmp dirs
    
    # args = parser.parse_args()
    
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
            ## all wrapper scripts will have to do output file naming, check if file exists, json info -- make those python scripts/functions that work with the bash scripts?
            ## would be like how Phil set up ants code, with bash scripts instead of a python library doing the actual processing
        print()
        print(f"Starting processing for subject {sub} session {ses}")

        ## TODO: t1preproc/ants require whole csv list, config script -- how to handle that set up?
        steptodo = "superres"
        submit_process_jobs(sub,ses,steptodo)
        # break

    # test = bids_image("/project/wolk_4/naccsc_bids/bids/sub-132132/ses-132132x20250407x3TxABCD2/anat/sub-132132_ses-132132x20250407x3TxABCD2_acq-800um_T1w.nii.gz")
    # test = bids_image("/project/wolk_4/naccsc_bids/bids/derivatives/superres/sub-131378/ses-131378x20250410x3TxABCD2/anat/sub-131378_ses-131378x20250410x3TxABCD2_acq-800um_desc-superres_T1w.nii.gz")
    # print(test.containing_bids_dir)
