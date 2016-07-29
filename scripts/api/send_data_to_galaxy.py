#!/usr/bin/env python
"""
This script uses the Galaxy API to create and populate Galaxy data libraries
with the data produced by sequencing runs.

Extreme care must be taken when creating the contents of the cegr_run_info
file as it is parsed and used to create data libraries and populate them with
files produced by sequencing runs.  In some cases, the file may have to be
edited manually.  When this is necessary, the file should be checked for
errors prior to running this script using the cegr_validate_run_info.py script.

Example of use: send_data_to_galaxy.py
"""

import sys
sys.path.insert(0, '../../util')
import api_util
import argparse
import os
import time
# If this Galaxy instance uses a virtual environment,
# activate it so we can import Galaxy from bioblend.
api_util.activate_virtual_env('PREP_VIRTUAL_ENV')
from bioblend import galaxy

SCRIPT_NAME = 'send_data_to_galaxy.py'

parser = argparse.ArgumentParser(description='Send sequenced data to Galaxy')
parser.add_argument("-a", "--api_key", dest="api_key", default=None, help="Galaxy API Key")
parser.add_argument("-c", "--cegr_run_info_file", dest="cegr_run_info_file", default=None, help="File contain run information")
parser.add_argument("-l", "--log_file", dest="log_file", default=None, help="File for storing logging output")
parser.add_argument("-p", "--prep_directory", dest="prep_directory", default=None, help="Directory containing datasets produced by cegr_fastq_merge.py")
parser.add_argument("-u", "--galaxy_base_url", dest="galaxy_base_url", default=None, help="Galaxy base URL")
args = parser.parse_args()

api_key = api_util.get_value_or_default(args.api_key, 'API_KEY')
cegr_run_info_file = api_util.get_value_or_default(args.cegr_run_info_file, 'RUN_INFO_FILE', is_path=True)
current_run_dir = api_util.get_current_run_directory(cegr_run_info_file)
current_run_folder = os.path.basename(current_run_dir)
galaxy_base_url = api_util.get_value_or_default(args.galaxy_base_url, 'GALAXY_BASE_URL')
gi = galaxy.GalaxyInstance(url=galaxy_base_url, key=api_key)
prep_directory = os.path.join(api_util.get_value_or_default(args.prep_directory, 'LIBRARY_PREP_DIR', is_path=True), current_run_folder)
log_dir = api_util.get_value_or_default(None, 'ANALYSIS_PREP_LOG_FILE_DIR', is_path=True, create_dir=True)
log_file = api_util.get_value_or_default(args.log_file, 'ANALYSIS_PREP_LOG_FILE', is_path=True)
lh = api_util.open_log_file(log_file, SCRIPT_NAME)

created_library_names = []
created_folder_names = []
current_run_dir = None
uploading_datasets = False

with open(cegr_run_info_file, 'r') as fh:
    for i, line in enumerate(fh):
        line = line.strip()
        if not line or line.startswith('#'):
            # Skip blank lines and comments.
            continue
        if current_run_dir is None:
            # The first non-blank, non-comment
            # line is the full path to the directory
            # on wall-E that contains the bcl files
            # for the run being processed.  Hopefully
            # this is a valid path.  There is no way
            # to test it here.
            current_run_dir = line
            lh.write('Directory on wall-E containing bcl files for run being processed:\n')
            lh.write('%s\n' % str(current_run_dir))
            continue
        items = line.split(';')
        if not api_util.check_run_info(line, items, lh, 'has_required_items', i):
            continue
        try:
            ok, tup = api_util.check_run_info(line, items, lh, 'parse', i)
            if ok:
                run, sample, indexes_str, wf_config_files, ext, data_lib_desc, data_lib_syn = tup
            else:
                continue
        except Exception as e:
            lh.write("\nError in check_run_info for line %d, exception:\n%s\n" % (i, str(e)))
            lh.write("Here is the line:\n")
            lh.write("%s\n" % line)
            continue
        try:
            if len(created_library_names) == 0:
                # Create a data library.
                if data_lib_desc == '':
                    data_lib_desc = None
                if data_lib_syn == '':
                    data_lib_syn = None
                new_lib_dict = gi.libraries.create_library(run, data_lib_desc, data_lib_syn)
                # Create a folder for the current sample.
                library_id = new_lib_dict['id']
                lh.write('Created new data library named "%s".\n' % run)
                created_library_names.append(run)
        except Exception as e:
            lh.write("\nError creating a data library for line %d, exception:\n%s\n" % (i, str(e)))
            lh.write("Here is the line:\n")
            lh.write("%s\n" % line)
            continue
        try:
            if sample not in created_folder_names:
                new_folder_dict = gi.libraries.create_folder(library_id, sample)[0]
                folder_id = new_folder_dict['id']
                lh.write('Created new data library folder named "%s".\n' % sample)
                created_folder_names.append(sample)
        except Exception as e:
            lh.write("\nError creating a folder for line %d, exception:\n%s\n" % (i, str(e)))
            lh.write("Here is the line:\n")
            lh.write("%s\n" % line)
            continue
        try:
            # Import all datasets contained within prep_directory for the current sample
            # into the sample folder within the data library.  The bcl2fastq step created
            # file names like this: 62401_S1_R1_001.fastq.gz
            for f in os.listdir(prep_directory):
                if f.startswith('%s-%s' % (run, sample)) and f.endswith('.fastq.gz'):
                    fpath = os.path.join(prep_directory, f)
                    # Import the dataset into the folder using fpath - don't set dbkey
                    # since samples are not associated with a genome until mapping.
                    lh.write('Uploading dataset to folder %s of library %s using path\n%s.\n' % (sample, run, fpath))
                    populate_folder_dict = gi.libraries.upload_file_from_local_path(library_id,
                                                                                    fpath,
                                                                                    folder_id=folder_id,
                                                                                    file_type='fastqsanger',
                                                                                    dbkey='?')
                    lh.write("\nResponse from uploading dataset:\n%s\n\n" % str(populate_folder_dict))
                    if not uploading_datasets:
                        uploading_datasets = True
        except Exception as e:
            lh.write("\nError importing datasets into folder for line %d, exception:\n%s\n" % (i, str(e)))
            lh.write("Here is the line:\n")
            lh.write("%s\n" % line)
if uploading_datasets:
    lh.write('\nSleeping for 30 minutes to make sure the data library upload jobs are finished...\n')
    time.sleep(1800)
    lh.write('Awake now...\n')
api_util.close_log_file(lh, SCRIPT_NAME)
# Let everyone know we've finished.
api_util.create_script_complete_file(log_dir, SCRIPT_NAME)
