#!/usr/bin/env python3

## each processing script as a function/module that could be imported/called
## these functions contain any of the specific-to-each-step inputs/outputs and call the bash scripts that do the processing 
## all receive same parameters: input, output, bsub_options

from naccsc_configs import *


def do_subprocess_run(list_of_args):
    ## list_of_args must have each bsub option as separate list item & args going to proc script
    try: 
        result = subprocess.run(list_of_args, capture_output=True, encoding="utf-8", timeout=10, check=True)
        result_list = result.stdout.split("\n")
        logging.info(result_list)
        if "Job <" in result_list[0]:
            return True
    except subprocess.CalledProcessError as exc:
        ## included because of check = True, if non-zero exit code
        logging.error(f"Process failed with non-zero exit code: {exc.returncode}\n{exc}\nError Message: {exc.stderr}")
    except subprocess.TimeoutExpired as exc:
        logging.error(f"Process timed out.\n{exc}")

## TODO: other info for json files?
def make_output_json_file(json_filepath, input_bids_uri, script_loc, specific_info):
    ## input_bids_uri is a list of bids-uri-formatted source files
    logging.debug(f"Making json file {json_filepath}")
    json_info = {"Sources": input_bids_uri, "ProcessDate": current_date_time, "Script": script_loc, **specific_info}
    logging.debug(f"Writing this info to the json: {json_info}")
    with open(json_filepath, "w") as file:
        json.dump(json_info, file, indent=4)
    return


def wrap_submit_t1icv(inputs, output, bsub_options):
    ## only 1 input file, used twice in call
    output_dir=output.image_dir
    id_opt=output.subject
    ashs_type = "ICV"
    allargs = ['bsub'] + bsub_options + ["bash", os.path.join(os.path.dirname(__file__),'ashs.sh'), ashs_root,
                 output_dir, ashs_type, f"-a {icv_atlas}", f"-g {inputs[0].file_hard_path}", 
                 f"-f {inputs[0].file_hard_path}", "-T", "-d", f"-I {id_opt}", f"-m {ashs_mopt_mat_file}", "-M"]
    job_submitted = do_subprocess_run(allargs)
    more_info = {
        "Atlas": icv_atlas
    }
    make_output_json_file(output.json_file, [input_image.bids_uri for input_image in inputs], ashs_root, more_info)   
    if job_submitted:
        return output.job_name
    else:
        return


def wrap_submit_superres(inputs, output, bsub_options):
    script_filepath=os.path.join(os.path.dirname(__file__),"superres_just_bash_parts.sh")    
    allargs = ['bsub'] + bsub_options + ["bash", script_filepath, inputs[0].file_hard_path, output.file_hard_path]
    job_submitted = do_subprocess_run(allargs)
    
    more_info = {}
    make_output_json_file(output.json_file, [input_image.bids_uri for input_image in inputs], "", more_info)
        ## but I really need the SRPATH value that's coded in the script itself now...
    if job_submitted:
        return output.job_name
    else:
        return ## returns [None] to run.py


def wrap_submit_T1ASHS(inputs, output, bsub_options):
    ## check that both inputs were found 
    if len(inputs) != 2:
        logging.info(f"Incorrect number of inputs. Need 2, passed inputs were: {[input_image.file_hard_path for input_image in inputs]}")
        return
    
    ## set up ashs options
    gopt_stepname = proc_steps[output.this_step]['input_files'][0]
    gopt_desc_keyword = proc_steps[gopt_stepname]['filters']['desc']
    gopt_nifti = [input_image.file_hard_path for input_image in inputs if gopt_desc_keyword in input_image.file_hard_path][0] # gopt, t1 image

    fopt_stepname = proc_steps[output.this_step]['input_files'][1]
    fopt_desc_keyword = proc_steps[fopt_stepname]['filters']['desc']
    fopt_nifti = [input_image.file_hard_path for input_image in inputs if fopt_desc_keyword in input_image.file_hard_path][0] #fopt, t2 image

    output_dir=output.image_dir
    id_opt=output.subject
    ashs_type = "T1ext"
    ## send to ashs script with ashs root and output directory and ashstype as first 3 positional args, then everything else as ashs call set up
    ## add arg to ashs.sh that is which kind of ashs, use that keyword for tmpdir cleanup. 
    ## pass from here, which is already separated into each type of ashs, can be consistent with any other wrapper script
 
    allargs = ['bsub'] + bsub_options + ["bash", os.path.join(os.path.dirname(__file__),'ashs.sh'), ashs_root,
                 output_dir, ashs_type, f"-a {ashs_t1ext_atlas}", f"-g {gopt_nifti}", 
                 f"-f {fopt_nifti}", "-T", "-d", f"-I {id_opt}", f"-m {ashs_mopt_mat_file}", 
                 "-M", f"-C {t1extashs_qc_slice_config}"]
    job_submitted = do_subprocess_run(allargs)

    more_info = {
        "Atlas": ashs_t1ext_atlas
    }
    make_output_json_file(output.json_file, [input_image.bids_uri for input_image in inputs], ashs_root, more_info)
    ## output json should always be generated, so there's a record of what files have been tried even if the job fails
    ## each new run generates a new json file, overwriting the old one
    
    if job_submitted:
        return output.job_name
    else:
        return


def wrap_submit_T2ASHS(inputs, output, bsub_options):
    ## check that both inputs were found 
    if len(inputs) != 2:
        logging.info(f"Incorrect number of inputs. Need 2, passed inputs were: {[input_image.file_hard_path for input_image in inputs]}")
        return
    
    ## set up ashs options
    gopt_stepname = proc_steps[output.this_step]['input_files'][0]
    gopt_desc_keyword = proc_steps[gopt_stepname]['filters']['desc']
    gopt_nifti = [input_image.file_hard_path for input_image in inputs if gopt_desc_keyword in input_image.file_hard_path][0] # gopt, t1 image
    fopt_nifti = [input_image.file_hard_path for input_image in inputs if "T2w" in input_image.file_hard_path][0] #fopt, t2 image    
    output_dir=output.image_dir
    id_opt=output.subject
    ashs_type = "T2"

    allargs = ['bsub'] + bsub_options + ["bash", os.path.join(os.path.dirname(__file__),'ashs.sh'), ashs_root,
                 output_dir, ashs_type, f"-a {ashs_t2_atlas}", f"-g {gopt_nifti}", 
                 f"-f {fopt_nifti}", "-T", "-d", f"-I {id_opt}", f"-m {ashs_mopt_mat_file}", "-M"]
    job_submitted = do_subprocess_run(allargs)
    more_info = {
        "Atlas": ashs_t2_atlas
    }
    make_output_json_file(output.json_file, [input_image.bids_uri for input_image in inputs], ashs_root, more_info)
    if job_submitted:
        return output.job_name
    else:
        return
    




### basic structure of all functions:
# def wrap_submit_t1icv(inputs, output, bsub_options):
#     allargs = ['bsub'] + bsub_options + ["bash", os.path.join(os.path.dirname(__file__),'ashs.sh'), ashs_root,
#                  output_dir, ashs_type, f"-a {ashs_t1ext_atlas}", f"-g {gopt_nifti}", 
#                  f"-f {fopt_nifti}", "-T", "-d", f"-I {id_opt}", f"-m {ashs_mopt_mat_file}", 
#                  "-M", f"-C {t1extashs_qc_slice_config}"]
#     job_submitted = do_subprocess_run(allargs)
#     more_info = {
#         "Atlas": ashs_t1ext_atlas
#     }
#     make_output_json_file(output.json_file, [input_image.bids_uri for input_image in inputs], ashs_root, more_info)
#     if job_submitted:
#         return output.job_name
#     else:
#         return
