#!/usr/bin/env python3

## inputs passed to the script
# input file = (str) just the file name in bids format e.g "sub-131378_ses-131378x20250410x3TxABCD2_acq-800um_desc-preproc_T1w.nii.gz"
# output_file_filters = (dict) key:value pairs of bids entities to use in output file name e.g. '{"desc" : "superres"}'
## uses file names only, no directories


import argparse 
import json

def get_new_file_name(input_file_name,output_file_filters):
    ## read input file into dict
    ## use negative one to prevent error on suffix that doesn't have a -
    input_file_dict = {e.split("-")[0]:e.split("-")[-1] for e in input_file_name.split("_")}
    output_file_dict = input_file_dict.copy()

    ## if key == value, it's a suffix--save as variable, drop from dict, add variable to end of final output file name
    suffix = [key for key in output_file_dict.keys() if key == output_file_dict[key]][0]
    output_file_dict.pop(suffix)

    ## compare input and output entities
    for key in output_file_filters.keys():
        output_file_dict[key] = output_file_filters[key]

    output_file_name = "_".join([f"{key}-{output_file_dict[key]}" for key in output_file_dict.keys()]) + "_" + suffix
    print(output_file_name)
    return
    # return output_file_name

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file_name", type=str, required=True, help="string of just the file name in bids format e.g 'sub-131378_ses-131378x20250410x3TxABCD2_acq-800um_desc-preproc_T1w.nii.gz'")
    parser.add_argument("-o", "--output_entities", type=json.loads, required=True, help="dictionary of bids entities to replace or add to file name. Quotes must be formatted as '{\"key\":\"value\"}' in command line to be read by json.loads")

    args=parser.parse_args()
  
    input_file_name = args.input_file_name
    output_entities = args.output_entities

    get_new_file_name(input_file_name,output_entities)
    ## does this need to be a function within the script? 
   
