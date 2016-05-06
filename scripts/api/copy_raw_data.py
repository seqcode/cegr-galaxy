#!/usr/bin/env python
"""
This script copies a directory of raw data files produced by the sequencer
from a remote host to a local directory.

Example of use: python copy_raw_data.py
"""

import sys
sys.path.insert(0, '../../util')
import api_util
import argparse
import os
import time

SCRIPT_NAME = 'copy_raw_data.py'

parser = argparse.ArgumentParser(description='Execute the copy raw data')
parser.add_argument("-c", "--cegr_run_info_file", dest="cegr_run_info_file", default=None, help="File contain run information")
parser.add_argument("-f", "--run_complete_file", dest="run_complete_file", default=None, help="File produced by sequencer when run is complete")
parser.add_argument("-l", "--log_file", dest="log_file", default=None, help="File for storing logging output")
parser.add_argument("-r", "--raw_data_directory", dest="raw_data_directory", default=None, help="Directory containing datasets produced by the sequencer")
parser.add_argument("-s", "--raw_data_login", dest="raw_data_login", default=None, help="Login to remote server containing raw data from sequencer")
args = parser.parse_args()

cegr_run_info_path = api_util.get_value_or_default(args.cegr_run_info_file, 'RUN_INFO_FILE', is_path=True)
log_dir = api_util.get_value_or_default(None, 'ANALYSIS_PREP_LOG_FILE_DIR', is_path=True, create_dir=True)
log_file = api_util.get_value_or_default(args.log_file, 'ANALYSIS_PREP_LOG_FILE', is_path=True)
lh = api_util.open_log_file(log_file, SCRIPT_NAME)
raw_data_directory = api_util.get_value_or_default(args.raw_data_directory, 'RAW_DATA_DIR', is_path=True)
raw_data_login = api_util.get_value_or_default(args.raw_data_login, 'RAW_DATA_LOGIN')
remote_run_info_file = api_util.get_value_or_default(None, 'REMOTE_RUN_INFO_FILE')
run_complete_file_name = api_util.get_value_or_default(args.run_complete_file, 'REMOTE_RUN_COMPLETE_FILE')

while True:
    if api_util.exists_remote(raw_data_login, remote_run_info_file, lh):
        if api_util.copy_remote_file(raw_data_login, remote_run_info_file, cegr_run_info_path, lh):
            cegr_run_info_file = cegr_run_info_path
        else:
            lh.write('Error copying file\n%s\nfrom host\n%s\nto local file\n%s\n\n' % (remote_run_info_file, raw_data_login, cegr_run_info_path))
            api_util.close_log_file(lh, SCRIPT_NAME)
            sys.exit(1)
        current_run_dir = api_util.get_current_run_directory(cegr_run_info_file)
        if current_run_dir is None:
            lh.write('\nRequired entry for current_run_dir missing from cegr_run_info.txt (this should be the first non-blank non-comment line in the file).\n')
            api_util.close_log_file(lh, SCRIPT_NAME)
            sys.exit(1)
        run_complete_file_path = os.path.join(current_run_dir, run_complete_file_name)
        lh.write('Current run directory on remote server: %s\n' % current_run_dir)
        if api_util.exists_remote(raw_data_login, run_complete_file_path, lh):
            rc = api_util.copy_remote_directory_of_files(raw_data_login, current_run_dir, raw_data_directory, lh)
            if rc == 0:
                # All files were successfully copied, so remove the remote cegr_run_info.txt file.
                rc = api_util.remove_remote_file(raw_data_login, remote_run_info_file, lh)
                if rc == 0:
                    # Let everyone know we've finished.
                    api_util.create_script_complete_file(log_dir, SCRIPT_NAME)
                    break
                else:
                    lh.write('Error removing file %s from remote server, return code: %d.\n' % (remote_run_info_file, rc))
                    api_util.close_log_file(lh, SCRIPT_NAME)
                    sys.exit(1)
            else:
                lh.write('Error copying raw data files from remote server, return code: %d.\n' % rc)
                api_util.close_log_file(lh, SCRIPT_NAME)
                sys.exit(1)
        else:
            lh.write('The file named\n%s\ndoes not exist on remote host %s, so the run must not be complete - will check again in 5 minutes.\n' % (run_complete_file_path, raw_data_login))
            time.sleep(300)
    else:
        lh.write('The file\n%s\ndoes not exist on remote host %s, so will check again in 5 minutes.\n' % (remote_run_info_file, raw_data_login))
        time.sleep(300)

api_util.close_log_file(lh, SCRIPT_NAME)
