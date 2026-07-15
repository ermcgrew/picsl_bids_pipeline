#!/usr/bin/env python3

print(f"importing {__name__}")

toplevelvar="in the init of picsl_bids_pipeline"
import global_configs, picsl_bids_pipeline
# from . import global_configs
# import .global_configs
# print(dir())
# import picsl_bids_pipeline
# from picsl_bids_pipeline import start_processing