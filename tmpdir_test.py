#!/usr/bin/env python3

## only need the tmpdir version right before using bidslayout, not necessary otherwise, right?
   ## make sure to use real bids path when making image class though
## is the tmpdir a full copy, or just symlinks? 
## need to include dataset_description.json (probably)

## use tempfile as: "context manager"
    #  with tempfile as varname:
        ## do all the stuff I need tempfile for
## wraps all the finding inputs stuff
## and the 1 find output line



import tempfile

with tempfile.TemporaryDirectory() as tmpbids:
    ## symlink subject's dirs to tmpbids
    
