#!/usr/bin/bash

import argparse
import bids
import json
import os
import pandas as pd
from pprint import pprint
from naccsc_configs import *

bids.config.set_option('extension_initial_dot', True)

# class bidsimage():
#     def __init__(self, data_path, sub, ses):
#         self.bids_dir_hard_filepath = data_path
#         self.sub = sub
#         self.session = ses

#     def get_original_nifti(self, **filters):
#         layout = bids.BIDSLayout(self.bids_dir_hard_filepath)
#         # print(f"using filters {filters}")

#         bids_matches = layout.get(subject=self.sub, session = self.session, extension='.nii.gz', return_type="filename", **filters)
#         ### returns a list
#         # print(bids_matches)
#         if len(bids_matches) == 1:
#             self.original_nifti=bids_matches[0]
#         elif len(bids_matches) > 1:
#             print("returning first match but there's more than one")
#             self.original_nifti=bids_matches[0]
#         else:
#             self.original_nifti=""


# don't do layout.get in class, pass the filepath for the image to the class
class testbidsimage():
    def __init__(self,filepath_to_image):
        self.file_hard_path = filepath_to_image
        self.subject = [x.split("-")[1] for x in filepath_to_image.split("/") if "sub" in x][0]
        self.session = [x.split("-")[1] for x in filepath_to_image.split("/") if "ses" in x][0]
        self.containing_bids_dir = os.path.dirname(self.file_hard_path)
        

      ## can deriv_nifti be a function of this class? 
      ## does one bids image ever have more than one derivative? filters should be set so there is only one image match
        ## if more than one match, skip and print error message

    def get_deriv_file(self, deriv_dir_name, **filters):
        layout = bids.BIDSLayout(bids_dir_filepath, derivatives=True)
        self.get_data_description(deriv_dir_name) ## read dataset_description.json for pipeline name to pass to layout.get scope arg
        ## subject and session already in filters subject=self.subject, session = self.session, 
        bids_matches = layout.get(extension='.nii.gz', return_type="filename", **filters, scope=self.pipeline_desc_name)
        if len(bids_matches) == 1:
            # self.deriv_nifti=bids_matches[0]
            return bids_matches[0]
        elif len(bids_matches) > 1:
            print(f"More than one match using filters {filters}, only one match allowed")
            # self.deriv_nifti=bids_matches[0]
            return False
        else:
            # self.deriv_nifti=""
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


# class deriv_nifti(bidsimage):

#     def get_deriv_file(self, deriv_dir_name, **filters):
#         layout = bids.BIDSLayout(self.bids_dir_hard_filepath, derivatives=True)
#         self.get_data_description(deriv_dir_name) ## read dataset_description.json for pipeline name to pass to layout.get scope arg
#         bids_matches = layout.get(subject=self.sub, session = self.session, extension='.nii.gz', return_type="filename", **filters, scope=self.pipeline_desc_name)
#         if len(bids_matches) == 1:
#             self.deriv_nifti=bids_matches[0]
#         elif len(bids_matches) > 1:
#             print("returning first match but there's more than one")
#             self.deriv_nifti=bids_matches[0]
#         else:
#             self.deriv_nifti=""

#     def get_data_description(self, deriv_dir_name = ""):
#         if deriv_dir_name:
#             filepath_to_join = f"{self.bids_dir_hard_filepath}/derivatives/{deriv_dir_name}"
#         else:
#             filepath_to_join = self.bids_dir_hard_filepath

#         try: 
#             with open(os.path.join(filepath_to_join, "dataset_description.json"), 'r') as file:
#                 data_descript = json.load(file)
#             self.pipeline_desc_name = data_descript['PipelineDescription']['Name']
#         except FileNotFoundError:
#             print("a dataset description.json file must exist for the derivative pipeline output.")
#             self.pipeline_desc_name = "" #set to empty so class doesn't error out when trying to use self.pipeline_desc_name
#             ## will error out if no 'outputs exist yet, which is fine, because then the output files are definitely missing and the deriv pipeline needs to be run.


def get_images(data_dir_filepath, filters, search_derivatives=False):
    layout = bids.BIDSLayout(data_dir_filepath, derivatives=search_derivatives)
    allimages = layout.get(return_type = "filename", extension = ["nii.gz", "nii"], **filters, invalid_filters="allow")
    print(allimages)
    bidsimage_objects = []
    for image in allimages:
        bidsimage_objects.append(testbidsimage(image))
    return bidsimage_objects


def run_pipeline():
    csvtoread = "/project/wolk_4/naccsc_bids/lists/sm_testlist.csv"
    # csvtoread = "/project/wolk_4/naccsc_bids/lists/EG_20250625_NACCSC.csv"
    df=pd.read_csv(csvtoread, header=None, names = ['ID','SESSIONNAME'])

    for index,row in df.iterrows():
        sub = row['ID']
        session = row['SESSIONNAME']        
        print(f"Running processing for {sub}, {session}...")

        ### for each sequence type of T1 T2 FLAIR (PET?)
            ## separate class instances for each sequence type
            ## use a session class object to build the bidsimage objects for each sequence type?

        ## design to process all T1w by default, with optional bids_filter to select specific acquisitions
        ## need to add option for x specific t1s (e.g. 800um and MPRAGE acq)? 

        t1filter = {**{"session":f"{session}", "subject":f"{sub}"}, **basic_t1w_filters}

        genfilter_list = []
        try: 
            for i in range(0,len(custom_t1w_filters)):
                genfilter_list.append({**t1filter, **custom_t1w_filters[i]})
        except NameError as e:
            genfilter_list.append(t1filter)
        
        for i in range(0,len(genfilter_list)): 
            ##  produces list of t1w images each as an instantiation of the class
            t1wlist = get_images(bids_dir_filepath, genfilter_list[i])
            if len(t1wlist) > 0:
                filters_to_use = genfilter_list[i]
                break

        for i in t1wlist:
            print(f"Do processing steps for file {i.file_hard_path}")
            for steptodo in processing_steps:
                print(steptodo)
                ## check for output first
                ## use base filters plus only filters for each step
                # i.get_deriv_file(processing_steps[steptodo]['dirname'], **{**filters_to_use,**processing_steps[steptodo]['filters']}) 
                this_step_output = i.get_deriv_file(processing_steps[steptodo]['dirname'], **{**filters_to_use,**processing_steps[steptodo]['filters']}) 
                # print(i.deriv_nifti)
                # if os.path.isfile(i.deriv_nifti):
                # print("inputs to get_deriv_file")
                # print(processing_steps[steptodo]['dirname'])
                # print(filters_to_use)
                # print(processing_steps[steptodo]['filters'])
                print(f"this_step_output equals: {this_step_output}")
                if os.path.isfile(this_step_output):
                    print("output already exists")
                else:
                    print(f"Need to run processing step {steptodo}")
                    ## t1wpreproc & ANTs run differently -- collect sub or sub,sess in to new csv to submit as one job
                    if steptodo == "T1w_preproc" or "ANTs" in steptodo:
                        print(f"Add {sub},{session} to csv for running t1wpreproc or ANTs")
                        ##TODO: define csv file, write to it, add option after all loops to call t1preproc/ANTs submit scripts
                        ## add values for the config scripts required by harmonized_submit_scripts to my config? or keep separate?
                        ## CRASHS 
                    else:
                        ## this would be easier if all our scripts took the same arguments...is it possible to make that modification?
                        ## could also send to wrapper scripts that finagle naming from simple inputs? 
                        ## 1 superres, 3 ASHS calls, flair skull stip, CRASHS and hd-bet use alist, pmatu, maybe prc_cleanup & infcereb?
                        ## superres and ASHS as containers w/ versioning? 
                        ## CRASHS current set-up uses a list, could probably modify it to be a one-off 
 
                        
                        outputdir=""
                        input_step_key=processing_steps[steptodo]['input_step']
                        this_step_input = i.get_deriv_file(processing_steps[input_step_key]['dirname'], **{**filters_to_use,**processing_steps[input_step_key]['filters']}) 
                        # print(i.deriv_nifti)
                        print(f"input file: {this_step_input}")


                        ## passed args for standardized wrappers: bids_input_dir bids_output_dir filters(sub, ses, etc) 
                        ## don't need to use exact file names because the wrapper scripts should have the bids filters built in
                        # or have a separate utility that sorts out all the names then passes to existing scripts? no
                        ## function for each pipeline to set up call, using pybids utilities? 

                        
        break


def submit_process_jobs(csv):
    df=pd.read_csv(csv, header=None, names = ['ID','SESSIONNAME'])

    for index,row in df.iterrows():
        sub = row['ID']
        ses = row['SESSIONNAME']    
        print(f"Starting processing for subject {sub} session {ses}")
        steptodo = "superres"

                    
        ## does set up for output happen here in wrapper, or in each processing script? 
            ## make sure dir exists, set up output file name (input | sed s/input/output/ & sed s/desc-input/desc-output/ ??)
        output_dir=f"{bids_dir_filepath}/derivatives/{processing_steps[steptodo]['output_dir_name']}/sub-{sub}/ses-{ses}/anat"
        if not os.path.exists(output_dir):
            print(f"Making output directory {output_dir}")
            os.makedirs(output_dir)


        ## using basc_t1w filter variable -- does that need to be separate, or include it in processing steps dict? 
        ## keep basic_t1w filter var & create reference to it from processing_steps dir
        ## processing_steps dir gets filled in from a bids_filter file? or is that dict the bids filter file separately from the rest of the configs?

        ## have some filters set to be the default with option to replace all with your own set? 

        # superres_bids_filters={"datatype":"anat", "suffix":"T1w", "session":f"{ses}", "subject":f"{sub}", "desc": "preproc", "acquisition":"800um"} 
        superres_bids_filters={**{"session":f"{ses}", "subject":f"{sub}", "acquisition":"800um"},**basic_t1w_filters,**processing_steps[steptodo]['input_filters']}        
        # print(superres_bids_filters)
        ## how to include acquisition? -- try with 800um first, then if no input_file results, try with MPRAGE, if still no, then no input? 
        input_files = get_images(bids_dir_filepath, superres_bids_filters, True)
        # print(len(input_files))
        
        for i in input_files:
            print(f"use this input file: {i.file_hard_path}")
            os.system(f"bash bids_superres.sh {i.file_hard_path} {output_dir}")


    return 


if __name__ == "__main__":

    # parser = argparse.ArgumentParser()
    # # parser.add_argument("-", "--", help="")
    # args = parser.parse_args()

    # print("Running run.py")
    # run_pipeline()

    ## two ways to do it--here's all the possible sessions, get a list of which need to be done, submit the list for processing 
    ## or, here's the list of sessions to be done, submit it

    # picsl_processing()
    ## always need to submit a csv (ID, MRIDATE | sometimes PETDATE )
    ## use csv as-is or parse for to-dos: store True to run function for parsing for to-dos (required to chose one or the other)
    ## which steps to do: chose from list: t1, t2, flair,diffusion,pet-mri reg*
    ## or can give more granular step options (optional) for each sequence type processing
    ## dry run option -- don't submit anything (use this for just parsing the csv for a to-do list) 
        ## (set dry run as default? have to pass a particular flag to actually submit)
    ## config file with filepaths
    ## bids filter json 

    ##function to match MRI to PET dates for registration 

    ## separate script: parse /bids folder for complete session lists -- 
        ## similar to /project/wolk_4/naccsc_bids/scripts/dcm2bids_scripts/tabulate_dcm2bids_helper.py 
        ## that can run on ADNI data as well, not wrapped inside of dcm2bids tmp dirs
    

    ## to call superres script: 
    ## send t1trim filepath, output directory to bids_superres.sh (one at a time)
    ## from list (assume doing all)
    ## check for bids filter
    ## use pybids to get t1trim filepath
    ## output dir is determined in config file
    csv="/project/wolk_4/naccsc_bids/lists/sm_testlist.csv"
    submit_process_jobs(csv)

    # testbidsimage("/project/wolk_4/naccsc_bids/bids/sub-132132/ses-132132x20250407x3TxABCD2/anat/sub-132132_ses-132132x20250407x3TxABCD2_acq-800um_T1w.nii.gz")
    