#!/usr/bin/env python3

import argparse
from datetime import datetime
import flywheel
import os
import pandas as pd

pd.options.mode.chained_assignment = None #suppresses setting with copy warning 
currentdatetime = datetime.now().strftime("%Y%m%d_%H%M")


last_updated_date = datetime.strptime("2025-07-08_+00:00", "%Y-%m-%d_%z")
list_dir="/project/wolk_4/naccsc_bids/lists/flywheel_sessions"
naccsc_fw_proj_id = "5c508d5fc2a4ad002d7628d8"
naccsc_sesslist_fw_view_id = "68af17ee9c4865a0929acef8" 


def main():
    fw = flywheel.Client()
    view = fw.get_view(naccsc_sesslist_fw_view_id)
    df = fw.read_view_dataframe(view, naccsc_fw_proj_id)

    ## filter out any duplicate, incomplete, techdev tags
    tmp = df.loc[pd.notnull(df['session.tags'])]
    tmp['session.tags'] = tmp['session.tags'].astype(str)
    todrop = tmp.loc[(tmp['session.tags'].str.lower().str.contains("incomplete")
                ) | (tmp['session.tags'].str.lower().str.contains("duplicate")
                ) | (tmp['session.tags'].str.lower().str.contains("techdev")
                ) | (tmp['session.tags'].str.lower().str.contains("misc"))].index.tolist()
    print(f"Dropping {len(todrop)} sessions that are tagged 'Incomplete', 'Duplicate', 'Misc.', or 'Techdev'")
    df = df.drop(todrop)

    df = df.sort_values(by=["subject.label","session.label"]).reset_index(drop=True)
    df.to_csv(os.path.join(list_dir,f"naccsc_allsessions_{currentdatetime}.csv"),index=False,header=True)

    df['session.created.dt'] = pd.to_datetime(df['session.created'],format="%Y-%m-%dT%H:%M:%S.%f%z",utc=True)
    df[['ID','DATE','SCANTYPE','STUDY']] = df['session.label'].str.rsplit("x",n=3,expand=True)

    new = df.loc[df['session.created.dt'] >= last_updated_date]
    print(f"{len(new)} new sessions since last update on {last_updated_date}")
    print(f"Most recent scan: {new.loc[new['session.created.dt'] == new['session.created.dt'].max(),"session.label"].values[0]}")
    print(f"New scans by scan type:")
    print(new['SCANTYPE'].value_counts(dropna=False))
    new[["subject.label","session.label"]].to_csv(os.path.join(list_dir,f"naccsc_new_sessions_{currentdatetime}.csv"),index=False,header=False)


main()