## Bids filtering

Two variables in `naccsc_configs.py` are available to set bids filtering: `basic_bids_filters` and `input_filters`/`output_filters` dictionaries in `processing_steps` dictionary. 

`basic_bids_filters` should contain bids values that will be the same for every processing step for a given image type. e.g., datatype: anat for all T2w images, or acquisition: 800um$|MPRAGE1mm for all T1w images.

`input_filters`/`output_filters` dictionaries contain bids entities that change values between inputs and outputs of processing steps. e.g. the value of "desc" for the superres step is "preproc" for input, and "superres" for output. 

Bids filter values can be modified from the default PICSL values currently found in `naccsc_configs.py` for other users/labs as needed. e.g. If you wanted to run superres step on the original un-trimmed T1w image, remove "desc: preproc" from superres['input_filters'].

## Processing steps handled in this script, in order

Indentation indicates which steps need to be completed so their output can be used as input. 

- t1w_preproc 
    - cross ANTs   
        - longANTs
            - parcellation 
                - inf_cereb_mask
                - structure stats from ANTs 
                - pmtau (?)
    - t1icv
    - superres
        - t1ext_ashs
            - crashs
            - T1 ASHS & CRASHS stats
    - t2ashs
        - prc_cleanup
            - t2 ashs stats
    - t1_pet_reg
        - t1_pet_suvr
            - pet_reg_qc
            - pet-mri stats
- flair_skull_strip 
    - wmh_seg
        - wmh stats
