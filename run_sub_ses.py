#!/usr/bin/bash

from naccsc_configs import *
from wrap_submit_scripts import wrap_submit_superres, wrap_submit_T1ASHS

# pass a filepath for an image
class bids_image():
    def __init__(self,filepath_to_image):
        self.file_hard_path = filepath_to_image
        self.subject = [x.split("-")[1] for x in self.file_hard_path.split("/") if "sub" in x][0]
        self.session = [x.split("-")[1] for x in self.file_hard_path.split("/") if "ses" in x][0]
        self.image_dir = os.path.dirname(self.file_hard_path)
        self.sub_ses_datatype_dirs = f"sub-{self.image_dir.split("/sub-")[-1]}"
        self.containing_bids_dir = self.file_hard_path.split("/sub-")[0] ## gets just the bids dir if raw, with derivative/name if derivative
        self.deriv_dir_name = self.containing_bids_dir.split("/")[-1]
        self.log_file = os.path.join(self.containing_bids_dir,"code","logs",f"{self.deriv_dir_name}_{self.subject}_{self.session}_{current_date_time}_%J.txt")
        self.json_file = self.file_hard_path.replace("nii.gz","json")
        self.bids_uri = f"bids::sub-{self.file_hard_path.split("/sub-",1)[-1]}" #format as: bids:ds000001:sub-02/anat/sub-02_T1w.nii.gz
        self.filename = os.path.basename(self.file_hard_path)
        self.runnum = [x for x in self.filename.split("_") if "run" in x]

        self._match_file_to_step()
        if self.runnum:
            self.job_name = f"{self.subject}_{self.session}_{self.runnum[0]}_{self.this_step}"
        else:
            self.job_name = f"{self.subject}_{self.session}_{self.this_step}"

    def make_session_dirs(self):
        try:
            os.makedirs(self.image_dir)
        except FileExistsError as e:
            logger.debug(f"Directory {self.image_dir} already exists.")
        return 

    ## compare deriv_dir_name to proc_steps[x]['directory'] - x is matching step name 
    def _match_file_to_step(self):
        if self.deriv_dir_name == "bids":
            self.this_step = "initial_input"
        else:
            for step in proc_steps.keys():
                if proc_steps[step]['directory'] == f"derivatives/{self.deriv_dir_name}":
                    self.this_step = step
                    break        
        return


def make_bids_dir(step):
    dir_to_make = os.path.join(bids_dir_filepath, proc_steps[step]['directory'])
    if not os.path.exists(dir_to_make):
        logger.debug(f"Making bids directory {dir_to_make}")
        os.makedirs(f"{dir_to_make}/code/logs/")
        if not os.path.exists(f"{dir_to_make}/dataset_description.json"):
            make_dataset_descript_json(dir_to_make,step)
    else:
        logger.debug("directory already exists")
    return 


def make_dataset_descript_json(dirpath,step):
    print('you have to make a dataset description json for the directory')
    ### TODO: how to write json file info. need script information from processing_steps, date? 
    return


## use pybids library to get filepaths for existing bids files and create bids_image objects
## to access derivative files, pass the derivative directory and validate = False
## will return an empty list if no files found
def get_images(data_dir_filepath, filters, validate_bids=False):
    layout = bids.BIDSLayout(data_dir_filepath, validate = validate_bids)
    allimages = layout.get(return_type = "filename", extension = ["nii.gz", "nii"], **filters, invalid_filters="allow", regex_search = True)
    bidsimage_objects = []
    for image in allimages:
        bidsimage_objects.append(bids_image(image))
    return bidsimage_objects


## use pybids library to get bids file names files that don't yet exist, then create bids_image objects
## outputdir must be the exact directory containing the file, e.g. bids/derivatives/pipeline1/sub-01/ses-01/anat
def build_bids_filepath(outputdir, this_step_filters_output):
    pattern = "sub-{subject}[_ses-{session}][_desc-{description}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_desc-{desc}]_{suffix}.nii.gz"
    layout = bids.BIDSLayout(outputdir, validate = False)
    output_file = bids_image(layout.build_path(this_step_filters_output, pattern, validate=False))
    return output_file


## filter for 800um, MPRAGE priority
def t1w_priority(image_objects=[]):
    eight_check = [i for i in image_objects if "800um" in i.file_hard_path]
    if len(eight_check) > 0:
        return eight_check
    else:
        mprage_check = [i for i in image_objects if "MPRAGE" in i.file_hard_path]
        if len(mprage_check) > 0: 
            return mprage_check
        else:
            logging.debug(f"No 800um or MPRAGE acquisitions found.")
            return


## set up common bids attributes before calling specific processing script with any particulars 
def submit_process_jobs(sub,ses,steptodo,wait_jobids):  
    
    ## TODO: copy just the files for sub into a tmpdir to speed up bids_layout 

    ## Get input file(s)--filtering for two kinds of files: duplicate runs & all necessary input files    
    inputfiles=[]
    for ift in proc_steps[steptodo]['input_files']:
        this_step_filters_input = {**proc_steps[ift]['filters'], **{"session":f"{ses}", "subject":f"{sub}"}}
        logging.info(f"Using filters: {this_step_filters_input} to find input image")
        found_files = get_images(os.path.join(bids_dir_filepath,proc_steps[ift]['directory']), this_step_filters_input)

        ## if no inputs found, but input/parent step in jobs_running list, use build_path to get image name for submission
        if len(found_files) == 0:
            parent_step_name = proc_steps[ift]['directory'].split("/")[-1]
            if len([j for j in wait_jobids if parent_step_name in j]) > 0:
                logging.info(f"Input file for {ift} doesnt' exist yet, input step running as part of this command")
                ## get acq and desc value in filters correct -- go back to bids folder and filter for acq priority
                ogfiles = get_images(os.path.join(bids_dir_filepath), {**basic_bids_filters['t1w'], **{"session":f"{ses}", "subject":f"{sub}"}})
                if this_step_filters_input['suffix'] == "T1w":
                    og_filtered = t1w_priority(ogfiles) 
                    og_filters = parse_file_entities(og_filtered[0].file_hard_path)
                    # any keywords in inputfilters that aren't in test, add them for build filters
                    for key in this_step_filters_input.keys():
                        if key not in og_filters.keys():
                            og_filters[key] = this_step_filters_input[key]
                    input_filepath = build_bids_filepath(os.path.join(bids_dir_filepath,proc_steps[ift]['directory']), og_filters)                
                    inputfiles.append(input_filepath) 
            else:
                logging.info(f"Missing input file for step {ift} and that step not in current run.")
                return [] 
        else:
            ## NOTE: pybids regex on acquisition still returning both T1w values instead of only 1, might be fixable in the future
            if this_step_filters_input['suffix'] == "T1w":
                filtered_files = t1w_priority(found_files) # takes list of objects, returns updated list
                if filtered_files == None:
                    logging.info(f"no appropriate T1 input file for step {ift}")
                    return [] 
                else:
                    inputfiles = inputfiles + filtered_files
            else:
                inputfiles = inputfiles + found_files


    this_sess_jobs=[]

    ### Account for multiple runs of same image type so each run will be processed separately, using a list of lists that have image objects 
    runcheck=[x for x in inputfiles if "run" in x.file_hard_path]
    if len(runcheck) >= 1:
        run_values = sorted(set([str(parse_file_entities(x.file_hard_path)['run']) for x in inputfiles]))
        ## set because otherwise multiple inputs and runs will increase the actual number of runs, str because zero-padded int is not a great data type
        runs=[]
        for value in run_values:
            runs.append([x for x in inputfiles if f"run-{value}" in x.file_hard_path])
    else:
        runs = [inputfiles]

    for i in range(0,len(runs)):
        logging.info(f"setting up processing for run # {i}")
        inputs = runs[i]
        logging.info(f"All input files: {[(i.file_hard_path) for i in inputs]}")    

        ## set up output directory path and output filters
        outputdir=os.path.join(bids_dir_filepath,proc_steps[steptodo]['directory'])
   
        ### Adjust filters for output file: parse_bids_entities(input) to get acq- and possibly run- values
        output_filters = {**proc_steps[steptodo]['filters'], **{"session":f"{ses}", "subject":f"{sub}"}}
        input_filters = parse_file_entities(inputs[0].file_hard_path)
        output_filters['acquisition'] = input_filters['acquisition']
        if "run" in input_filters.keys():
            output_filters['run'] = input_filters['run']

        ### Quick check for output file
        if output_check == True:
            logging.info(f"running output check for files matching filters: {output_filters}")
            output_files = get_images(outputdir,output_filters)
            file_check = [os.path.isfile(o.file_hard_path) for o in output_files]
            if True in file_check:
                logging.info(f"Output file already exists, not submitting the job.")
                continue 
        
        ## get filepath for output file 
        output_file = build_bids_filepath(os.path.join(outputdir,inputs[0].sub_ses_datatype_dirs), output_filters)
        if not dry_run:
            output_file.make_session_dirs() 

        ## set up bsub options -- now separating bsub flags from their args in list
        submit_options = ["-o", output_file.log_file, "-J", output_file.job_name, "-w", f"ended(control_{sub}_{ses}*)"]
        
        if wait_jobids:
            ## filter out other run numbers from jobid list
            if output_file.runnum:
                jobids_touse = [w for w in wait_jobids if output_file.runnum[0] in w]
            else: 
                jobids_touse = wait_jobids

            for i in range(0,len(jobids_touse)):
                submit_options[-1] = submit_options[-1] + f" && ended({jobids_touse[i]})"

        ## call step-specific wrap script to set up any other args & submit job to cluster 
        if steptodo == "superres":
            this_sess_jobs.append(wrap_submit_superres(inputs, output_file, submit_options))
        elif steptodo == "t1ext_ashs":
            this_sess_jobs.append(wrap_submit_T1ASHS(inputs, output_file, submit_options))
    
    return this_sess_jobs


if __name__ == "__main__":

    ### TODO: change structure:run.py == picsl_bids_pipeline, __init__ file with imports & other global stuff from configs.py 

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--sub", help = "")
    parser.add_argument("-e", "--ses", help = "")
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
  
    ## put args.stepstodo in order
    arg_steps_ordered = [step_ordered for step_ordered in proc_steps.keys() for arg_step in args.stepstodo if step_ordered == arg_step]

    ## Set up bids directories & dataset_description.json for each step
    dry_run = args.dry_run
    if not dry_run:
        for step in args.stepstodo: 
            make_bids_dir(step)
    
    ## Set whether or not to check for output before submitting processing jobs
    if args.skip_output_check == True:
        output_check = True
    else:
        output_check = False

    logging.info(f"Starting processing for subject {args.sub} session {args.ses}")
    jobs_running = {}
    for steptodo in arg_steps_ordered:
        logging.info(f"Processing step {steptodo}...")
        ## TODO: t1preproc/ants require whole csv list, config script -- handle that setup differently?
        input_steps = proc_steps[steptodo]['input_files']
        for i in input_steps:
            if i in jobs_running.keys():
                wait_jobids = jobs_running[i]
            else:
                wait_jobids = []    
        jobidnum = submit_process_jobs(args.sub,args.ses,steptodo,wait_jobids)
        jobs_running[steptodo] = jobidnum
     

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
