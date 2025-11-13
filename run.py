#!/usr/bin/bash

# from bids import BIDSLayout
import bids
import os
import pandas as pd
from pprint import pprint

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

    def get_deriv_file(self, deriv_pipeline_name, **filters):
        ## set derivatives to True for now with derivative pipeline name
        layout = bids.BIDSLayout(self.bids_dir_hard_filepath,derivatives=True)
        bids_matches = layout.get(subject=self.sub, session = self.session, extension='.nii.gz', return_type="filename", **filters, scope=deriv_pipeline_name)
        if len(bids_matches) == 1:
            self.deriv_nifti=bids_matches[0]
        elif len(bids_matches) > 1:
            print("returning first match but there's more than one")
            self.deriv_nifti=bids_matches[0]
        else:
            self.deriv_nifti=""


# processing_steps=["neck_trim", "cortical_thick", "brain_ex", "whole_brain_seg", "wbseg_to_ants", 
#             "wbsegqc", "inf_cereb_mask", "pmtau", 
#             "t1icv", "superres", "t1ashs", "t1ext_ashs", "t1mtthk", "t2ashs","prc_cleanup",
#             "flair_skull_strip", "wmh_seg",
#             "t1_pet_reg", "t1_pet_suvr", "pet_reg_qc",
#             "ashst1_stats", "ashst2_stats", "wmh_stats", "structure_stats", "pet_stats",
#             "adhoc_run_pet", "adhoc_mri"]
processing_steps=["T1w_preproc","crossANTs","t1icv"] 


### config stuff
bids_dir_filepath = "/project/wolk_4/naccsc_bids/bids"

t1w_preproc_bids_filter = {"datatype":"anat", "suffix":"T1w"} ## T1preproc files ending in T1w are the desc files, no other files in t1_preproc ouput match that 
t1w_icv_bids_filter = {"datatype":"anat", "suffix":"T1w", "description":"ashsicv"}


if __name__ == "__main__":
    df=pd.read_csv("/project/wolk_4/naccsc_bids/lists/EG_20250625_NACCSC.csv",header=None,names=['ID','SESSIONNAME'])
    for index,row in df.iterrows():
        sub = row['ID']
        session = row['SESSIONNAME']

        print(sub, session)

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

        print(bids_image_object.original_nifti)


        steptodo = "t1_preproc"
        if steptodo == "t1_preproc":
            ## check for output first:
            deriv_pipeline_name = "NACC-SC_BIDS T1w Preprocessed"
            bids_image_object.get_deriv_file(deriv_pipeline_name, **t1w_preproc_bids_filter)
            if len(bids_image_object.deriv_nifti) > 0:
                print(bids_image_object.deriv_nifti)
            else:
                print(f'no output, find input file to run step {steptodo}')



