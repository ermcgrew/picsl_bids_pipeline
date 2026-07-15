#!/usr/bin/env python3
print(f"importing {__name__}")
## each processing script as a function/module that could be imported/called
## these functions contain any of the specific-to-each-step inputs/outputs and call the bash scripts that do the processing 
## all receive same parameters: input, output, bsub_options

from global_configs import *


def do_subprocess_run(list_of_args):
    ## list_of_args must have each bsub option as separate list item & args going to proc script
    try: 
        result = subprocess.run(list_of_args, capture_output=True, encoding="utf-8", timeout=10, check=True)
        result_list = result.stdout.split("\n")
        print(result_list)
        if "Job <" in result_list[0]:
            return True
            # jobidnum=result_list[0].split("<")[1].split(">")[0]
    except subprocess.CalledProcessError as exc:
        ## included because of check = True, if non-zero exit code
        print(f"Process failed with non-zero exit code: {exc.returncode}\n{exc}\nError Message: {exc.stderr}")
    except subprocess.TimeoutExpired as exc:
        print(f"Process timed out.\n{exc}")


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
    ##TODO: check length of inputs list or length of list comprehension? 
    ## Also i don't love the use of bids entity keywords here for distinguishing files, but order not guaranteed(?)
    ## TODO: use step keywords to access input step 'desc' keyword? 
    # input_step_keyword = input_image.this_step['input_files']
    # input_step_keyword['filters']['desc']
    ## order not guaranteed-- what if superres keyword first and that's what gets searched for in t1 image opt?

    t1trim_nifti = [input_image.file_hard_path for input_image in inputs if "preproc" in input_image.file_hard_path][0] # gopt, t1 image
    superres_nifti = [input_image.file_hard_path for input_image in inputs if "superres" in input_image.file_hard_path][0] #fopt, t2 image
    output_dir=output.image_dir
    id_opt=output.subject
    ashs_type = "T1ext"
    ## send to ashs script with ashs root and output directory and ashstype as first 3 positional args, then everything else as ashs call set up
    ## add arg to ashs.sh that is which kind of ashs, use that keyword for tmpdir cleanup. 
    ## pass from here, which is already separated into each type of ashs, can be consistent with any other wrapper script
 
    allargs = ['bsub'] + bsub_options + ["bash", os.path.join(os.path.dirname(__file__),'ashs.sh'), ashs_root,
                 output_dir, ashs_type, f"-a {ashs_t1ext_atlas}", f"-g {t1trim_nifti}", 
                 f"-f {superres_nifti}", "-T", "-d", f"-I {id_opt}", f"-m {ashs_mopt_mat_file}", 
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


def wrap_submit_T2_ASHS():
    print("this is the t2 ashs function in test.py")

    return
