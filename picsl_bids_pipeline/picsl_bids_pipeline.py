#!/usr/bin/bash
print(f"importing {__name__}")
avar = "variable in picsl_bids_pipeline top file"

from global_configs import *
# from wrap_submit_scripts import wrap_submit_superres, wrap_submit_T1ASHS
# import process_helpers
from process_scripts.process_helpers import submit_process_jobs

# if __name__ == "__main__":
def start_processing():

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help = "Csv of sub,ses without header.")
    parser.add_argument("-s", "--stepstodo", help = "Processing step to run", choices = proc_steps.keys(), 
                        nargs = "+") ##TODO: fix formatting on choices, printing as dict then list with dict in help function
    parser.add_argument("-d", "--dry_run", action = "store_true", help = "Dry run this script without submitting any processing jobs.")
    parser.add_argument("-k", "--skip_output_check", action = "store_false", help = "Default behavior is to check for existing output before submitting a job. Include this flag to skip check.")
    
    ## always need to submit a csv (SUB, SES)
        ## Don't need to have versions with mridate AND petdate as input -- have that match determined within registration scripts    
    ## TODO: which steps to do: chose from list: t1, t2, flair,diffusion,pet-mri reg* as mutually exclusive arg group with granular stepstodo
    ## TODO: config file with filepaths -- as arg, or keep as import like currently?

    ## TODO: function to match MRI to PET dates for registration 
    ## TODO: function for selecting to-do sessions: give directory path and check for completion
    ## TODO: separate script/function parse /bids folder for complete session lists -- 
        ## similar to /project/wolk_4/naccsc_bids/scripts/dcm2bids_scripts/tabulate_dcm2bids_helper.py 
        ## that can run on ADNI data as well, not wrapped inside of dcm2bids tmp dirs
    
    args = parser.parse_args()

    ## check that csv path is real
    # csvtoread="/project/wolk_4/naccsc_bids/lists/sm_testlist.csv"
    # csvtoread="/project/wolk_4/naccsc_bids/lists/rerun_one.csv"
    csvtoread = args.csv
    if not os.path.isfile(csvtoread):
        logging.info(f"filepath {csvtoread} does not exist.")
        raise SystemExit(1)
  
    ## put args.stepstodo in order
    arg_steps_ordered = [step_ordered for step_ordered in proc_steps.keys() for arg_step in args.stepstodo if step_ordered == arg_step]

    ## Set up bids directories & dataset_description.json for each step
    dry_run = args.dry_run
    # if not dry_run:
    #     for step in args.stepstodo: 
    #         make_bids_dir(step)
    
    ## Set whether or not to check for output before submitting processing jobs
    if args.skip_output_check == True:
        output_check = True
    else:
        output_check = False
  
    ## Read csv for sub,ses to process
    df=pd.read_csv(csvtoread, header=None, names = ['ID','SESSIONNAME'])
    for index,row in df.iterrows():
        jobs_running = {}
        sub = row['ID']
        ses = row['SESSIONNAME']    
        ## TODO: spin off each sub/ses to go through the process parallelly instead of sequentially?
            # one master job for each sub,ses  to run -- all steps to do coordinated through that job
        print()
        print(f"Starting processing for subject {sub} session {ses}")

        for steptodo in arg_steps_ordered:
            ## TODO: t1preproc/ants require whole csv list, config script -- handle that setup differently?
            input_steps = proc_steps[steptodo]['input_files']
            for i in input_steps:
                if i in jobs_running.keys():
                    wait_jobids = jobs_running[i]
                else:
                    wait_jobids = []    
            jobidnum = submit_process_jobs(sub,ses,steptodo,wait_jobids)
            jobs_running[steptodo] = jobidnum
        break 

    # test = bids_image("/project/wolk_4/naccsc_bids/bids/sub-132132/ses-132132x20250407x3TxABCD2/anat/sub-132132_ses-132132x20250407x3TxABCD2_acq-800um_T1w.nii.gz")
    # test = bids_image("/project/wolk_4/naccsc_bids/bids/derivatives/superres/sub-131378/ses-131378x20250410x3TxABCD2/anat/sub-131378_ses-131378x20250410x3TxABCD2_acq-800um_desc-superres_T1w.nii.gz")
    # test = bids_image("/project/wolk_4/naccsc_bids/bids/derivatives/superres/sub-132455/ses-132455x20250414x3TxABCD2/anat/sub-132455_ses-132455x20250414x3TxABCD2_acq-800um_run-01_desc-superres_T1w.nii.gz")
    # print(test.job_name)
    # print(test.sub_ses_datatype_dirs)
    # print(test.file_hard_path)
    # print(test.json_file)
    # print(test.this_step)
    # print(test.containing_bids_dir)
    # print(test.log_file)
