#!/usr/bin/env python
import sys
sys.path.insert(0, '../../util')
import api_util
import data_library_util
import history_util
import workflow_util
import argparse
import os
import time
# If this Galaxy instance uses a virtual environment,
# activate it so we can import Galaxy from bioblend.
api_util.activate_virtual_env('PREP_VIRTUAL_ENV')
from bioblend import galaxy

"""
This script parses the cegr_run_info.txt file to automatically execute a
selected workflow for each dbkey defined for every sample in the defined run.
This script follows the execution of the send_data_to_galaxy.py script.  This
script retrieves library datasets that were imported by that script and imports
them into a new history for each workflow execution.  The history is named with
a combination of the workflow name (e.g., sacCer3_cegr_paired), the workflow
version (e.g., 001) the sample (e.g., 02) and the history name id (e.g., 001).
Using these examples, the complete history name is
sacCer3_cegr_paired_001-02_001.  The values of both the workflow version and
the history name id can be passed as command line parameters if desired.

This script requires the following conditions to function as expected.
1) If the "-b" command line parameter is not used, then the data library that
   contains the blacklist filter datasets for each build is assumed to be named
   "Blacklist Filter".  This default can be changed in the default setting in
   the api_util.py script.
2) The blacklist filter dataset name must start with the value of the dbkey
   (e.g., sacCer3_cegr, hg19, etc).
3) The blacklist filter dataset must exist in the root folder of the blacklist
   filter data library.
4) The blacklist filter input dataset in the workflow must have the exact label
   "blacklist".
5) Each workflow config XML file defines a workflow execution.
6) Each input dataset defined within a workflow must have a workflow label
   (e.g., R1) that is contained within the names of the input dataset (e.g.,
   60642_R1.fq).

Example of use: start_workflow.py
"""

SCRIPT_NAME = 'start_workflows.py'

parser = argparse.ArgumentParser(description='Execute one or more Galaxy workflows baes on the contents of a selected data library')
parser.add_argument("-a", "--api_key", dest="api_key", default=None, help="Galaxy API Key")
parser.add_argument("-b", "--blacklist_filter_library_name", dest="blacklist_filter_library_name", default=None, help="Name of the Galaxy data library folder containing the blacklist filter datasets")
parser.add_argument("-c", "--cegr_run_info_file", dest="cegr_run_info_file", default=None, help="File contain run information")
parser.add_argument("-i", "--history_name_id", dest="history_name_id", default="001", help="Galaxy history name identifier")
parser.add_argument("-l", "--log_file", dest="log_file", default=None, help="File for storing logging output")
parser.add_argument("-r", "--raw_data_directory", dest="raw_data_directory", default=None, help="Directory containing datasets produced by the sequencer")
parser.add_argument("-u", "--galaxy_base_url", dest="galaxy_base_url", default=None, help="Galaxy base URL")
parser.add_argument("-v", "--workflow_version", dest="workflow_version", default="001", help="Galaxy workflow version")
parser.add_argument("-w", "--remote_workflow_config_dir_name", dest="remote_workflow_config_dir_name", default=None, help="Name of directory containing the workflow config XML files produced by PEGR")
args = parser.parse_args()

api_key = api_util.get_value_or_default(args.api_key, 'API_KEY')
blacklist_filter_library_name = api_util.get_value_or_default(args.blacklist_filter_library_name, 'BLACKLIST_FILTER_LIBRARY_NAME')
cegr_run_info_file = api_util.get_value_or_default(args.cegr_run_info_file, 'RUN_INFO_FILE', is_path=True)
current_run_dir = api_util.get_current_run_directory(cegr_run_info_file)
current_run_folder = os.path.basename(current_run_dir)
galaxy_base_url = api_util.get_value_or_default(args.galaxy_base_url, 'GALAXY_BASE_URL')
gi = galaxy.GalaxyInstance(url=galaxy_base_url, key=api_key)
log_dir = api_util.get_value_or_default(None, 'ANALYSIS_PREP_LOG_FILE_DIR', is_path=True, create_dir=True)
log_file = api_util.get_value_or_default(args.log_file, 'ANALYSIS_PREP_LOG_FILE', is_path=True)
lh = api_util.open_log_file(log_file, SCRIPT_NAME)
raw_data_directory = os.path.join(api_util.get_value_or_default(args.raw_data_directory, 'RAW_DATA_DIR', is_path=True), current_run_folder)
remote_workflow_config_dir_name = api_util.get_value_or_default(args.remote_workflow_config_dir_name, 'REMOTE_WORKFLOW_CONFIG_DIR_NAME')
workflow_config_directory = os.path.join(raw_data_directory, remote_workflow_config_dir_name)
workflow_invocation_dbkeys = api_util.get_config_settings(type='workflow_invocation')
workflow_names = api_util.get_config_settings(type='workflows')
workflow_version = api_util.get_value_or_default(args.workflow_version, 'WORKFLOW_VERSION')

NO_INVOCATION_DBKEYS = workflow_invocation_dbkeys['NO_INVOCATION']

run_dir_processed = False
can_archive_cegr_run_info_file = True

with open(cegr_run_info_file, 'r') as fh:
    for i, line in enumerate(fh):
        line = line.strip()
        if not line or line.startswith('#'):
            # Skip blank lines and comments.
            continue
        if not run_dir_processed:
            # The first non-blank, non-comment
            # line is the full path to the directory
            # on wall-E that contains the bcl files
            # for the run being processed.  Hopefully
            # this is a valid path.  There is no way
            # to test it here.
            run_dir_processed = True
            continue
        items = line.split(';')
        if not api_util.check_run_info(line, items, lh, 'has_required_items', i):
            continue
        try:
            ok, tup = api_util.check_run_info(line, items, lh, 'parse', i)
            if ok:
                run, sample, indexes_str, wf_config_files_str, ext, data_lib_desc, data_lib_syn = tup
            else:
                continue
            indexes = indexes_str.split(',')
            wf_config_files = workflow_util.get_workflow_config_files(workflow_config_directory, wf_config_files_str)

            # Get the data library for the run.
            data_lib_id = data_library_util.get_data_library(gi, run, lh)
            if data_lib_id is None:
                lh.write('Skipping invalid line %d, it contains run %s but no data library with that name exists.\n' % (i, run))
                continue

            # Get the blacklist filter data library.
            blacklist_library_id = data_library_util.get_data_library(gi, blacklist_filter_library_name, lh)

            # Get the folder named the value of the sample.
            folder_id = data_library_util.get_folder(gi, data_lib_id, run, sample, lh)
            if folder_id is None:
                lh.write('Skipping invalid line %d, it contains sample %s but no folder with that name exists.\n' % (i, sample))
                continue

            # Get the workflow name.
            workflow_name, num_datasets = workflow_util.select_workflow(gi, folder_id, workflow_names, sample, run, lh)
            if workflow_name is None:
                lh.write('Skipping sample %s since the data library folder contains %d datasets when it should contain only 1 or 2.\n' % (sample, num_datasets))
                continue

            # Get the datasets from the current sample folder.
            lib_input_datasets = data_library_util.get_sample_datasets(gi, data_lib_id, sample, run, lh)

            # Prepare and execute a workflow for each wf_config_file.
            for wf_config_file in wf_config_files:
                dbkey, params = workflow_util.parse_workflow_config(wf_config_file, lh)
                if dbkey is None and params is None:
                    lh.srite('Skipping line %d since workflow config %s is either missing or invalid.\n' % (i, wf_config_file))
                if dbkey in NO_INVOCATION_DBKEYS:
                    lh.write('Skipping line %d containing workflow config %s with dbkey %s because workflows are not to be executed for that dbkey.\n' % (i, wf_config_file, dbkey))
                    continue
                lh.write('\nPreparing analysis pipeline for workflow config file %s.\n' % wf_config_file)
                blacklist_filter_dataset_id = data_library_util.get_blacklist_filter_dataset_id(gi, blacklist_library_id, dbkey, lh)
                if blacklist_filter_dataset_id is None:
                    lh.write('Skipping line %d containing workflow config %s with dbkey %s since no blacklist filter dataset for that dbkey exists but one is required.\n' % (i, wf_config_file, dbkey))
                    continue

                # Get the workflow.
                workflow_id, workflow_dict = workflow_util.get_workflow(gi, workflow_name, lh)
                if workflow_id is None:
                    lh.write('Skipping invalid line %d, it contains workflow config %s with invalid workflow name %s.\n' % (i, wf_config_file, workflow_name))
                    continue

                # Update the params if possible.
                # TODO: this is extremely brittle and should be eliminated asap.
                params = workflow_util.update_workflow_params(dbkey, workflow_dict, params, lh)
                lh.write("Sleeping for 10 seconds...\n")
                time.sleep(10)

                # Create a new history to contain the analysis
                history_name, history_id = history_util.create_history(gi,
                                                                       dbkey,
                                                                       workflow_name,
                                                                       run,
                                                                       sample,
                                                                       args.history_name_id,
                                                                       lh)
                lh.write("Sleeping for 10 seconds...\n")
                time.sleep(10)

                history_input_datasets = {}
                # Add the blacklist filter dataset to the new history.
                history_input_datasets = history_util.add_library_dataset_to_history(gi,
                                                                                     dbkey,
                                                                                     history_id,
                                                                                     history_name,
                                                                                     blacklist_filter_dataset_id,
                                                                                     history_input_datasets,
                                                                                     lh)
                lh.write("Sleeping for 10 seconds...\n")
                time.sleep(10)

                # Populate the history with the input datasets for the sample.
                for input_dataset_id, input_dataset_name in lib_input_datasets.items():
                    history_input_datasets = history_util.add_library_dataset_to_history(gi,
                                                                                         dbkey,
                                                                                         history_id,
                                                                                         history_name,
                                                                                         input_dataset_id,
                                                                                         history_input_datasets,
                                                                                         lh)
                    lh.write("Sleeping for 10 seconds...\n")
                    time.sleep(10)
                history_input_datasets = history_util.update_dataset(gi,
                                                                     dbkey,
                                                                     history_id,
                                                                     history_name,
                                                                     history_input_datasets,
                                                                     lh)

                # Map the history datasets to the input datasets for the workflow.
                inputs = workflow_util.get_workflow_input_datasets(gi,
                                                                   history_name,
                                                                   history_input_datasets,
                                                                   workflow_name,
                                                                   dbkey,
                                                                   galaxy_base_url,
                                                                   api_key,
                                                                   lh)
                lh.write("inputs:\n%s\n" % str(inputs))
                lh.write("Sleeping for 10 seconds...\n")
                time.sleep(10)

                # Start the workflow.
                workflow_util.start_workflow(gi,
                                             workflow_id,
                                             workflow_name,
                                             inputs,
                                             params,
                                             history_id,
                                             lh)
                lh.write("Sleeping for 60 seconds...\n")
                time.sleep(60)
        except Exception, e:
            lh.write('\nError encountered in script start_workflows.py.\n')
            lh.write('%s\n' % str(e))
            can_archive_cegr_run_info_file = False
api_util.close_log_file(lh, SCRIPT_NAME)
if can_archive_cegr_run_info_file:
    # This is the last step in the automated processing
    # pipeline, so archive the cegr_run_info.xml file.
    api_util.archive_file(cegr_run_info_file, run)
# Let everyone know we've finished.
api_util.create_script_complete_file(log_dir, SCRIPT_NAME)
