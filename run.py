#!/usr/bin/bash

import argparse
import bids
import json
import os
import pandas as pd
from pprint import pprint
from naccsc_configs import *
from test import superres

bids.config.set_option('extension_initial_dot', True)


# don't do layout.get in class, pass the filepath for the image to the class
class bids_image():
    def __init__(self,filepath_to_image):
        self.file_hard_path = filepath_to_image
        self.subject = [x.split("-")[1] for x in self.file_hard_path.split("/") if "sub" in x][0]
        self.session = [x.split("-")[1] for x in self.file_hard_path.split("/") if "ses" in x][0]
        self.image_dir = os.path.dirname(self.file_hard_path)
        self.containing_bids_dir = self.file_hard_path.split("/sub-")[0] ## gets just the bids dir if raw, with derivative/name if derivative


    def get_deriv_file(self, deriv_dir_name, **filters):
        ## deriv file is not an attribute of the class, it's another instance of the class 
            ## allows for multiple deriv files to be determined for each file
            ## TODO: handling of multiple deriv matches -- not sure if allowing only 1 is the best move
        layout = bids.BIDSLayout(bids_dir_filepath, derivatives=True)
        self.get_data_description(deriv_dir_name) ## read dataset_description.json for pipeline name to pass to layout.get scope arg
        ## subject and session already in filters subject=self.subject, session = self.session, 
        bids_matches = layout.get(extension='.nii.gz', return_type="filename", **filters, scope=self.pipeline_desc_name)
        if len(bids_matches) == 1:
            return bids_image(bids_matches[0])
        elif len(bids_matches) > 1:
            print(f"More than one match using filters {filters}, only one match allowed")
            return False
        else:
            return False
    

    def get_data_description(self, deriv_dir_name = ""):
        if deriv_dir_name:
            filepath_to_join = f"{bids_dir_filepath}/derivatives/{deriv_dir_name}"
        else:
            filepath_to_join = bids_dir_filepath

        try: 
            with open(os.path.join(filepath_to_join, "dataset_description.json"), 'r') as file:
                data_descript = json.load(file)
            self.pipeline_desc_name = data_descript['PipelineDescription']['Name']
        except FileNotFoundError:
            print("a dataset description.json file must exist for the derivative pipeline output.")
            self.pipeline_desc_name = "" #set to empty so class doesn't error out when trying to use self.pipeline_desc_name
            ## will error out if no 'outputs exist yet, which is fine, because then the output files are definitely missing and the deriv pipeline needs to be run.

    ## TODO: have this run as part of init of class object instead of calling within script
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


def get_images(data_dir_filepath, filters, search_derivatives=False):
    layout = bids.BIDSLayout(data_dir_filepath, derivatives=search_derivatives)
    allimages = layout.get(return_type = "filename", extension = ["nii.gz", "nii"], **filters, invalid_filters="allow")
    # print(allimages)
    bidsimage_objects = []
    for image in allimages:
        bidsimage_objects.append(bids_image(image))
    return bidsimage_objects


def submit_process_jobs(sub,ses,steptodo):  
    '''sets up common bids attributes before calling specific processing script with any particulars'''
    
    ##### Get input file(s)
    ## TODO: using basc_t1w filter variable -- does that need to be separate, or include it in processing steps dict? 
        ## keep basic_t1w filter var & create reference to it from processing_steps dir
        ## processing_steps dir gets filled in from a bids_filter file? or is that dict the bids filter file separately from the rest of the configs?
    ## TODO: have some filters set to be the default with option to replace all with your own set? 
    t1filter = {**{"session":f"{ses}", "subject":f"{sub}"}, **basic_t1w_filters, **processing_steps[steptodo]['input_filters']}
    acq_preferred_filters = []
    try: 
        for i in range(0,len(custom_t1w_filters)):
            acq_preferred_filters.append({**t1filter, **custom_t1w_filters[i]})
    except NameError as e:
        acq_preferred_filters.append(t1filter)

    ## For each possible acq entity, check if bids image can be found
    for i in range(0,len(acq_preferred_filters)): 
        ## list of t1w images each as an instantiation of the class
        input_files = get_images(bids_dir_filepath, acq_preferred_filters[i], True)
        acq_entity=acq_preferred_filters[i]['acquisition']
        if len(input_files) > 0:
            print(f"found image with acquisition entity: {acq_entity}")
            filters_to_use = acq_preferred_filters[i] ### does this need to be saved as a variable??
            break
        elif i < (len(acq_preferred_filters) -1):
            print(f"no image matching {acq_entity}, searching for {acq_preferred_filters[i+1]['acquisition']}")
        else: 
            print(f"No image matched to passed filters: {acq_preferred_filters}")

    ## Run processing for each image found
    for i in input_files:
        print(f"use this input file: {i.file_hard_path}") 

        ##### get output file as another instance of bids image class
        output_file=i.get_deriv_file(processing_steps[steptodo]['output_dir_name'],**processing_steps[steptodo]['output_filters'])
        print(output_file.image_dir)

        ##### check if output exists already
        if os.path.isfile(output_file.file_hard_path):
            print(f"Output file {output_file.file_hard_path} already exists, exiting this step")
            break
        else:              
            ## make session output dir (this also checks the overall bids dir exists)
            output_file.make_session_dirs() 

            ##### set up json output for each output file
            make_dataset_descript_json(self.containing_bids_dir)

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

    # parser = argparse.ArgumentParser()
    # parser.add_argument("-c", "--csv", help = "Csv of sub,ses without header.", required = True)
    # parser.add_argument("-d", "--dry_run", action = "store_true", help = "Dry run this script without submitting any processing jobs.")
    # parser.add_argument("-s", "--select_todo_sessions", action = "store_true", help = "Check all sessions in the csv for any that need to be run and only submit jobs for those sessions instead of all sessions in csv.")

    ## always need to submit a csv (SUB, SES)
         ## not any versions with mridate and petdate as input -- have that match determined within registration scripts
    ## use csv as-is or parse for to-dos: store True to run function for parsing for to-dos (required to chose one or the other)
    ## TODO: for selecting to-do sessions, can also give directory path and check for completion?
    ## TODO: which steps to do: chose from list: t1, t2, flair,diffusion,pet-mri reg*
        ##  can give more granular step options (optional) for each sequence type processing
    ## dry run option -- don't submit anything 
    ## TODO: config file with filepaths
    ## TODO: bids filter json 

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
        print(f"Starting processing for subject {sub} session {ses}")

        ## TODO: t1preproc/ants require whole csv list, config script -- how to handle that set up?
        steptodo = "superres"
        submit_process_jobs(sub,ses,steptodo)
        # break

    # test = bids_image("/project/wolk_4/naccsc_bids/bids/sub-132132/ses-132132x20250407x3TxABCD2/anat/sub-132132_ses-132132x20250407x3TxABCD2_acq-800um_T1w.nii.gz")
    # test = bids_image("/project/wolk_4/naccsc_bids/bids/derivatives/superres/sub-131378/ses-131378x20250410x3TxABCD2/anat/sub-131378_ses-131378x20250410x3TxABCD2_acq-800um_desc-superres_T1w.nii.gz")
    # print(test.containing_bids_dir)
