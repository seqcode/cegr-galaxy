#!/usr/bin/env python
"""
This script reads a directory of raw files from the sequencer and executes
the bcl2fastq converter on each file

Example of use: python bcl2fastq.py
"""
import sys
sys.path.insert(0, '../../util')
import api_util
import argparse
import os

SCRIPT_NAME = 'bcl2fastq.py'

parser = argparse.ArgumentParser(description='Execute the bcl2fastq converter')
parser.add_argument("-b", "--bcl2fastq_binary", dest="bcl2fastq_binary", default=None, help="Path to bcl2fastq binary")
parser.add_argument("-c", "--cegr_run_info_file", dest="cegr_run_info_file", default=None, help="File contain run information")
parser.add_argument("-d", "--bcl2fastq_report_dir", dest="bcl2fastq_report_dir", default=None, help="Path to bcl2fastq reports root directory")
parser.add_argument("-l", "--log_file", dest="log_file", default=None, help="File for storing logging output")
parser.add_argument("-p", "--prep_directory", dest="prep_directory", default=None, help="Directory containing datasets produced by cegr_bcl2fastq.py")
parser.add_argument("-r", "--raw_data_directory", dest="raw_data_directory", default=None, help="Directory containing datasets produced by the sequencer")
parser.add_argument("-s", "--sample_sheet", dest="sample_sheet", default=None, help="The csv version of cegr_run_info.txt required by bcl2fastq")
args = parser.parse_args()

# The bcl2fastq binary must be available on the $PATH.  This is handled
# via modules on the ICS clusters, so this should not be sent as a path.
bcl2fastq_binary = api_util.get_value_or_default(args.bcl2fastq_binary, 'BCL2FASTQ_BINARY')
bcl2fastq_report_dir = api_util.get_value_or_default(args.bcl2fastq_report_dir, 'BCL2FASTQ_REPORT_DIR', is_path=True)
cegr_run_info_file = api_util.get_value_or_default(args.cegr_run_info_file, 'RUN_INFO_FILE', is_path=True)
current_run_dir = api_util.get_current_run_directory(cegr_run_info_file)
current_run_folder = os.path.basename(current_run_dir)
log_dir = api_util.get_value_or_default(None, 'ANALYSIS_PREP_LOG_FILE_DIR', is_path=True, create_dir=True)
log_file = api_util.get_value_or_default(args.log_file, 'ANALYSIS_PREP_LOG_FILE', is_path=True)
lh = api_util.open_log_file(log_file, SCRIPT_NAME)
prep_directory = os.path.join(api_util.get_value_or_default(args.prep_directory, 'LIBRARY_PREP_DIR', is_path=True), current_run_folder)
raw_data_directory = os.path.join(api_util.get_value_or_default(args.raw_data_directory, 'RAW_DATA_DIR', is_path=True), current_run_folder)
sample_sheet = api_util.get_value_or_default(args.sample_sheet, 'SAMPLE_SHEET', is_path=True)

# If we are processing run 209 or earlier, we'll need to copy the raw data directory
# from the old location to the new location.
rc = api_util.copy_raw_data_if_necessary(current_run_dir, raw_data_directory, lh)
if rc == 0:
    # Generate the sample sheet required by the Illumina bec2fastq binary.
    api_util.generate_sample_sheet(cegr_run_info_file, sample_sheet, lh)
    # Build the command.
    cmd = '%s ' % bcl2fastq_binary
    # Minimum log level, recognized values: NONE, FATAL, ERROR, WARNING, INFO, DEBUG, TRACE.
    cmd += '-l ERROR '
    # Path to input directory, default (=<runfolder-dir>/Data/Intensities/BaseCalls/).
    cmd += '-i %s/Data/Intensities/BaseCalls ' % raw_data_directory
    # Path to runfolder directory, default (=./).
    cmd += '-R %s ' % raw_data_directory
    # Path to demultiplexed output, default (=<input-dir>)
    cmd += '-o %s ' % prep_directory
    # Path to demultiplexing statistics directory, default (=<runfolder-dir>/InterOp/).
    cmd += '--interop-dir %s/InterOp ' % raw_data_directory
    # Path to human-readable demultiplexing statistics directory, default (=<output-dir>/Stats/).
    cmd += '--stats-dir %s/Stats ' % prep_directory
    # Path to reporting directory, default (=<output-dir>/Reports/).
    cmd += '--reports-dir %s/Reports ' % prep_directory
    # Do not split fastq files by lane.
    cmd += '--no-lane-splitting '
    # Path to the sample sheet.
    cmd += '--sample-sheet %s ' % sample_sheet
    # Tiles aggregation flag  determining structure of input files, recognized values: AUTO, YES, NO.
    # cmd += '--aggregated-tiles AUTO '
    # Number of threads used for loading BCL data.
    cmd += '-r 24 '
    # Number of threads used for demultiplexing.
    cmd += '-d 24 '
    # Number of threads used for processing demultiplexed data.
    cmd += '-p 24 '
    # number of threads used for writing FASTQ data this must not be higher than number of samples.
    cmd += '-w 24 '
    # Additional options not used here...
    # Number of allowed mismatches per index multiple entries, default (=1).
    cmd += '--barcode-mismatches 1'
    
    # Get the run from the sample sheet.
    run = api_util.get_run_from_sample_sheet(sample_sheet)
    
    # Errors will be logged by execute_cmd.
    rc = api_util.execute_cmd(cmd, lh)
    if rc == 0:
        # Move the bcl2fastq-generated "Reports" directory and its contents to long-term storage.
        src_path = os.path.join(prep_directory, 'Reports', 'html')
        dest_path = os.path.join(bcl2fastq_report_dir, run)
        rc = api_util.copy_local_directory_of_files(src_path, dest_path, lh)
    
    api_util.close_log_file(lh, SCRIPT_NAME)
    # Archive the sample sheet.
    api_util.archive_file(sample_sheet, run)
    
    if rc == 0:
        # Let everyone know we've finished.
        api_util.create_script_complete_file(log_dir, SCRIPT_NAME)
