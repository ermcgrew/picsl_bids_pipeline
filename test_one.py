#!/usr/bin/env python3

## from terminal with conda activate /project/wolk_4/emcgrew/picslbids/

import os
from run_sub_ses import get_images
sub="114000"
ses="114000x20220503x3TxABC"
stepstodo="t2ashs"


os.system(f"python /project/wolk_4/naccsc_bids/scripts/picsl_bids_pipeline/run_sub_ses.py \
            -u {sub} -e {ses} -s {stepstodo} -k")

get_images