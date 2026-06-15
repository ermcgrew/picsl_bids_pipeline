## User-defined inputs

Default values for PICSL processing in `naccsc_configs.py`, can be changed for other users.

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
