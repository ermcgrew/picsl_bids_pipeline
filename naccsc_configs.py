#!/usr/bin/env python3




bids_dir_filepath = "/project/wolk_4/naccsc_bids/bids"

# processing_steps=["neck_trim", "cortical_thick", "brain_ex", "whole_brain_seg", "wbseg_to_ants", 
#             "wbsegqc", "inf_cereb_mask", "pmtau", 
#             "t1icv", "superres", "t1ashs", "t1ext_ashs", "t1mtthk", "t2ashs","prc_cleanup",
#             "flair_skull_strip", "wmh_seg",
#             "t1_pet_reg", "t1_pet_suvr", "pet_reg_qc",
#             "ashst1_stats", "ashst2_stats", "wmh_stats", "structure_stats", "pet_stats",
#             "adhoc_run_pet", "adhoc_mri"]
processing_steps=["T1w_preproc","crossANTs","t1icv"] 



## for each processing step you're going to do, define the following in a dict? 
## bids filter, dirname, processing script?
t1w_preproc_bids_filter = {"datatype":"anat", "suffix":"T1w"} ## T1preproc files ending in T1w are the desc files, no other files in t1_preproc ouput match that 
t1w_preproc_dirname = "T1wPreprocessing_061"


t1w_icv_bids_filter = {"datatype":"anat", "suffix":"T1w", "description":"ashsicv"}
