#!/bin/bash
# copy of /project/hippogang_2/pauly/wolk/anterior_mtl/process_abc/scripts/runme.sh, edited

id=${1?}
sess=${2?}
ASHS_deriv_dir=${3?} # e.g /project/wolk_4/SCAN/bids/derivatives/ASHST1 


## Set up 
CRASHS_HOME=/project/hippogang_2/pauly/tk/crashs_v2
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
# activate your env
conda activate /project/wolk_4/emcgrew/new_crashs_python312


for side in left right ; do 

    ## define files
    fullid=${id}_${sess}_${side}
    ASHSDIR="${ASHS_deriv_dir}/sub-${id}/ses-${sess}/anat/ASHST1_anteriorMTL/ashs"
    CRASHS_DIR="${ASHS_deriv_dir}/sub-${id}/ses-${sess}/anat/ASHST1_anteriorMTL/crashs/crashs_${side}"

    # don't re-run if output exists already
    if [[ -f $CRASHS_DIR/thickness/${fullid}_thickness_roi_summary.csv ]]; then
        echo "Output already exists: ${CRASHS_DIR}/thickness/${fullid}_thickness_roi_summary.csv"
        exit 
    fi

    export PATH=$CRASHS_HOME/ext/Linux:$PATH
    mkdir -p $CRASHS_DIR
    rm -rf $CRASHS_DIR/*

    # Scratch working directory for all processing
    TMP_JOB_ROOT=$(mktemp -d /scratch/crashs_${fullid}_XXXXXX)
    TMP_OUT="${TMP_JOB_ROOT}/out"
    mkdir -p "$TMP_OUT"

    # We have to disable keops caching because of cluster clashing
    export KEOPS_CACHE_FOLDER=$(mktemp -d /scratch/keops_cache_XXXXXX)

    # This fixed a hard to track down double-free bug somewhere in the optimal
    # mass transport code that would occur only some of the time and only when
    # using the CPU. The bug is still lurking there somewhere...
    export PYTHONMALLOC=malloc

    # Run CRASHS 
    # Skip thickness
    python3 -m crashs fit -s $side --device cpu \
        -i ${fullid} -f bootstrap -c heur \
        --pruning-geodesic-factor 1.1 \
        --skip-thick \
        -C /project/hippogang_2/pauly/tk/crashs_template_package \
        $ASHSDIR ashs_pmc_t1ext $TMP_OUT

    # # Run thickness --> does not work in my own environment meshlab-py312 - I0 error
    # python3 -m crashs fit -s $side --device cpu \
    #     -i ${fullid} -f bootstrap -c heur \
    #     --pruning-geodesic-factor 1.1 \
    #     --skip-preproc --skip-cruise --skip-reg --skip-omt \
    #     -C /project/hippogang_2/pauly/tk/crashs_template_package \
    #     $ASHSDIR ashs_pmc_t1ext $TMP_OUT

# 2) Run thickness only, by calling compute_thickness_stats directly
python3 - << EOF
from crashs.util import CrashsDataRoot, Template, Workspace
import crashs.crashs as cr

crashs_data   = "/project/hippogang_2/pauly/tk/crashs_template_package"
template_name = "ashs_pmc_t1ext"
workdir       = "$TMP_OUT"
expid         = "$fullid"
side          = "$side"

# Recreate Template and Workspace like FitLauncher.run
cdr = CrashsDataRoot(crashs_data)
template_dir = cdr.find_template(template_name)
template = Template(template_dir)
ws = Workspace(workdir, expid, side)

cr.compute_thickness_stats(template, ws, pruning_geodesic_factor=1.1)
EOF

    # Key files to retain
    KEY_FILES=(
        cruise/${fullid}_mtl_cruise-cortex.nii.gz
        cruise/${fullid}_mtl_avg_l2m-mesh-ras.vtk
        fitting/${fullid}_fitted_dist_stat.json
        fitting/${fullid}_fit_target_reduced.vtk
        fitting/${fullid}_fitted_lddmm_template.vtk
        thickness/${fullid}_template_thickness.vtk
        thickness/${fullid}_thickness_roi_summary.csv)

    missing=0
    for rf in "${KEY_FILES[@]}"; do
    src="${TMP_OUT}/${rf}"
    dst="${CRASHS_DIR}/${rf}"
    if [[ -f "$src" ]]; then
        mkdir -p "$(dirname "$dst")"
        cp -p "$src" "$dst"
        # optional: verify copy
        [[ -s "$dst" ]] || { echo "ERROR: copied file is empty: $dst"; exit 3; }
    else
        echo "WARNING: expected file missing: $src"
        missing=$((missing+1))
    fi
    done

    rm -rf $TMP_OUT

    echo "Copied $((${#KEY_FILES[@]}-missing)) / ${#KEY_FILES[@]} key files to $CRASHS_DIR" 

    ## symlink output files to top level dir with bids names -- thickness_roi_summary.csv & fitted_dist_stat.json

done
