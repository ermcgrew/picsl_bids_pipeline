#!/usr/bin/bash

module load python
module unload miniconda 
module load miniconda/3-25
eval "$(conda shell.bash hook)"
conda activate /project/wolk_4/emcgrew/picslbids

csvtoread="/project/wolk_4/naccsc_bids/lists/sm_testlist.csv"
# csvtoread="/project/wolk_4/naccsc_bids/lists/rerun_one.csv"
currentdatetime=$( date '+%Y%m%d_%H%M')

## if step == t1wpreproc, ants, longants,parcants, 
## send csv and bids dir loc to harmonized submit scripts
## no tracking on the jobs? 

# stepstodo="t1icv"
# stepstodo="t2ashs"
stepstodo="flair_skull_strip"

cat $csvtoread | while read line ; do 
    sub=$( echo $line | cut -f 1 -d , )
    ses=$( echo $line | cut -f 2 -d , )
    echo Processing for $sub,$ses
    bsub -q bsc_short -J "control_${sub}_${ses}_${currentdatetime}" \
        -o "/project/wolk_4/naccsc_bids/scripts/pipeline_logs/${sub}_${ses}_${currentdatetime}.txt" \
        python /project/wolk_4/naccsc_bids/scripts/picsl_bids_pipeline/run_sub_ses.py \
        -u $sub -e $ses -s ${stepstodo} -k
    break
done

# sub="132132"
# ses="132132x20250407x3TxABCD2"
# sub="999999"
# ses="999999x20251113x3TxFAKE"
# bsub -q bsc_short -J "control_${sub}_${ses}_${currentdatetime}" -o "/project/wolk_4/naccsc_bids/scripts/pipeline_logs/${sub}_${ses}_${currentdatetime}.txt" 


