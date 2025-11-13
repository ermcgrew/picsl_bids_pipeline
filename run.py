#!/usr/bin/bash

import bids
import json
import os
import pandas as pd
from pprint import pprint
from naccsc_configs import *

bids.config.set_option('extension_initial_dot', True)

class bidsimage():
    def __init__(self, data_path, sub, ses):
        self.bids_dir_hard_filepath = data_path
        self.sub = sub
        self.session = ses

    def get_original_nifti(self, **filters):
        layout = bids.BIDSLayout(self.bids_dir_hard_filepath)
        # print(f"using filters {filters}")

        bids_matches = layout.get(subject=self.sub, session = self.session, extension='.nii.gz', return_type="filename", **filters)
        ### returns a list
        # print(bids_matches)
        if len(bids_matches) == 1:
            self.original_nifti=bids_matches[0]
        elif len(bids_matches) > 1:
            print("returning first match but there's more than one")
            self.original_nifti=bids_matches[0]
        else:
            self.original_nifti=""


    ## build_path for files that don't exist -- no, don't need this. if the file doesn't exist, layout.get return empty
    # filters.update({"sub":self.sub,ses:self.session})
    # bids_matches = layout.build_path(filters)

    def get_deriv_file(self, deriv_dir_name, **filters):
        layout = bids.BIDSLayout(self.bids_dir_hard_filepath, derivatives=True)
        self.get_data_description(deriv_dir_name) ## read dataset_description.json for pipeline name to pass to layout.get scope arg
        bids_matches = layout.get(subject=self.sub, session = self.session, extension='.nii.gz', return_type="filename", **filters, scope=self.pipeline_desc_name)
        if len(bids_matches) == 1:
            self.deriv_nifti=bids_matches[0]
        elif len(bids_matches) > 1:
            print("returning first match but there's more than one")
            self.deriv_nifti=bids_matches[0]
        else:
            self.deriv_nifti=""


    def get_data_description(self, deriv_dir_name = ""):
        if deriv_dir_name:
            filepath_to_join = f"{self.bids_dir_hard_filepath}/derivatives/{deriv_dir_name}"
        else:
            filepath_to_join = self.bids_dir_hard_filepath

        try: 
            with open(os.path.join(filepath_to_join, "dataset_description.json"), 'r') as file:
                data_descript= json.load(file)
            self.pipeline_desc_name = data_descript['PipelineDescription']['Name']
        except FileNotFoundError:
            print("a dataset description.json file must exist for the derivative pipeline output.")
            ## will error out if no 'outputs exist yet, which is fine, because then the output files are definitely missing and the deriv pipeline needs to be run.



def run_pipeline():
    df=pd.read_csv("/project/wolk_4/naccsc_bids/lists/EG_20250625_NACCSC.csv",header=None,names=['ID','SESSIONNAME'])
    for index,row in df.iterrows():
        sub = row['ID']
        session = row['SESSIONNAME']        
        print(f"Running processing for {sub}, {session}...")

        ## For now, let's pretend we'll process all T1w files present -- filtering is a question to discuss with Sandy?

        ## always set original bids image, then call another method on the class to get derivatives
            ## that would maybe handle the acq filtering?
            ### make this a try/except series, if no T1 found break T1 step loop
        filters = {"datatype":"anat", "suffix":"T1w" , "acquisition":"800umxND"}
        bids_image_object = bidsimage(bids_dir_filepath, sub, session)
        bids_image_object.get_original_nifti(**filters)
        if bids_image_object.original_nifti == "":
            bids_image_object=bidsimage("/project/wolk_4/naccsc_bids/bids", sub, session)
            filters={"datatype":"anat", "suffix":"T1w" , "acquisition":"MPRAGE1mm"}
            bids_image_object.get_original_nifti(**filters)

        print(f"Original T1 nifti: {bids_image_object.original_nifti}")

        ### For processing step:
        steptodo = "t1_preproc"
        if steptodo == "t1_preproc":
            ## check for output first:
            bids_image_object.get_deriv_file(t1w_preproc_dirname, **t1w_preproc_bids_filter)
            if len(bids_image_object.deriv_nifti) > 0:
                print(f"Derivative nifti: {bids_image_object.deriv_nifti}")
            else:
                print(f'no output, find input file to run step {steptodo}')



if __name__ == "__main__":
    print("Running run.py")
    run_pipeline()
    