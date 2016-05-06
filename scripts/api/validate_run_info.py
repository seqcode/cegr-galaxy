#!/usr/bin/env python
import argparse
import os
import sys

"""
This script validates the contents of the cegr_run_info.txt file.

Example of use: python validate_run_info.py -c cegr_run_info.txt
"""

parser = argparse.ArgumentParser(description='Validate cegr_run_ionfo.txt file')
parser.add_argument("-c", "--cegr_run_info_file", dest="cegr_run_info_file", required=True, help="File contain run information")
args = parser.parse_args()

current_run_dir = None
num_lines = 0
num_invalid_lines = 0
num_blank_lines = 0
num_comments = 0
num_runs = 0
num_samples = 0
num_known_datatypes = 0
num_unknown_datatypes = 0
num_wf_invocations = 0
num_unknown_dbkeys = 0
num_indexes = 0
run_names = []
sample_names = []
all_indexes = []
wf_invocations = []
warnings = []

cegr_run_info_file = args.cegr_run_info_file
# Assume the scripts are located in the current working directory.
script_dir = os.path.dirname(os.path.realpath(__file__))

with open(cegr_run_info_file, 'r') as fh:
    for line in fh:
        num_lines += 1
        line = line.strip()
        line = line.rstrip('\n')
        if not line:
            num_blank_lines += 1
            continue
        if line.startswith('#'):
            num_comments += 1
            continue
        if current_run_dir is None:
            # The first non-blank, non-comment
            # line is the full path to the directory
            # on wall-E that contains the bcl files
            # for the run being processed.  Hopefully
            # this is a valid path.  There is no way
            # to test it here.
            current_run_dir = line
            continue
        items = line.split(';')
        if not (len(items) >= 4 and len(items) <= 7):
            num_invalid_lines += 1
            warning = "Line %d is invalid, it must have between 4 and 7 strings separated by semicolons:\n" % num_lines
            warning += "Here is the line:\n"
            warning += "%s\n" % line
            warning += "%s\n" % str(items)
            warnings.append(warning)
        try:
            run = str(items[0]).strip()
            sample = str(items[1]).strip()
            indexes_str = str(items[2]).strip()
            wf_config_files = str(items[3]).strip()
            if not run:
                num_invalid_lines += 1
                warning = "Line %d is invalid, it does not contain a required run value:\n" % num_lines
                warning += "Here is the line:\n"
                warning += "%s\n" % line
                warnings.append(warning)
                continue
            if not sample:
                num_invalid_lines += 1
                warning = "Line %d is invalid, it does not contain a required sample value:\n" % num_lines
                warning += "Here is the line:\n"
                warning += "%s\n" % line
                warnings.append(warning)
                continue
            if run not in run_names:
                run_names.append(run)
                num_runs += 1
            if sample not in sample_names:
                sample_names.append(sample)
                num_samples += 1
            if indexes_str:
                indexes = indexes_str.split(',')
                for index in indexes:
                    if index not in all_indexes:
                        all_indexes.append(index)
                        num_indexes += 1
            else:
                num_invalid_lines += 1
                warning = "Line %d is invalid, it does not contain a required index value:\n" % num_lines
                warning += "Here is the line:\n"
                warning += "%s\n" % line
                warnings.append(warning)
                continue
            if wf_config_files:
                wf_configs = wf_config_files.split(',')
                for wf_config in wf_configs:
                    if wf_config not in wf_invocations:
                        wf_invocations.append(wf_config)
                        num_wf_invocations += 1
            else:
                num_invalid_lines += 1
                num_unknown_dbkeys += 1
                warning = "Line %d is invalid, it does not contain a required workflow payload file name:\n" % num_lines
                warning += "Here is the line:\n"
                warning += "%s\n" % line
                warnings.append(warning)
                continue
            if len(items) >= 5:
                ext = str(items[4]).strip()
                if ext not in ['', '?']:
                    num_known_datatypes += 1
                else:
                    num_unknown_datatypes += 1
            else:
                num_unknown_datatypes += 1
        except Exception, e:
            print "\nLine %d is invalid, exception: %s" % (num_lines, str(e))
            print "Here is the line:"
            print "%s\n" % line
            sys.exit(1)

print "\nResults for %s\n" % cegr_run_info_file
if num_invalid_lines == 0:
    print "\nGood news, the contents of the file look valid!\n\n"
else:
    print "\nBad news, one or more lines in the file look invalid!\n"
print "Number of lines: %d" % num_lines
print "Number of invalid lines: %d" % num_invalid_lines
print "Number of blank lines: %d" % num_blank_lines
print "Number of comment lines: %d" % num_comments
print "Full path to bcl files directory on wall-E: %s", current_run_dir
print "Number of runs defined: %d" % num_runs
print "Number of samples defined: %d" % num_samples
print "Number of indexes defined: %d" % num_indexes
print "Number of known datatypes defined: %d" % num_known_datatypes
print "Number of unknown datatypes that will be set to the default fastqsanger: %d" % num_unknown_datatypes
print "Number of workflow invocations defined: %d" % num_wf_invocations
print "\nNumber of warnings: %d" % len(warnings)
for warning in warnings:
    print "%s\n" % warning
print "\n"
