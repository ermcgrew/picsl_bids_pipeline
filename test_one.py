#!/usr/bin/env python3

## from terminal with conda activate /project/wolk_4/emcgrew/picslbids/

import os

sub="100905x01"
ses="100905x01x20260311x3TxCLARiTI"
# stepstodo="superres t1ext_ashs" #superres 
stepstodo="crashs"
os.system(f"python /project/wolk_4/naccsc_bids/scripts/picsl_bids_pipeline/run_sub_ses.py \
            -u {sub} -e {ses} -s {stepstodo} -d") #-k to skip output check
