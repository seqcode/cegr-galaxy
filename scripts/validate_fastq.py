"""
Can be used from the command line to validate a directory of fastq files.
For example:
python validate_fastq.py -p /prep_dir/160630_NS500168_0158_AH5HGWBGXY -r 211

The fastQValidator package is available here:
http://genome.sph.umich.edu/w/images/2/20/FastQValidatorLibStatGen.0.1.1a.tgz
Due to the way bcl2fastq compresses files (it does not include an end of file block),
this enhancement was added manually to the ~/src/FastQValidator.cpp file: 
https://github.com/statgen/fastQValidator/commit/0b7decb8b502cd8d9d6bf27dbd9e319ed8478b53.
The package was then compiled normally.
"""
import sys
sys.path.insert(0, '../util')
import api_util
import argparse
import glob
import os
import subprocess

parser = argparse.ArgumentParser(description='Validate fastq files')
parser.add_argument("-f", "--fastq_validator_binary", dest="fastq_validator_binary", default=None, help="Path to fastQValidator")
parser.add_argument("-p", "--prep_directory", dest="prep_directory", help="Full path to directory containing datasets produced by bcl2fastq")
parser.add_argument("-r", "--run", dest="run", help="Run number")
args = parser.parse_args()

ALL_VALID = True
CONFIG_FILE = '../config/cegr_config.ini'
CONFIG_SETTINGS = api_util.get_config_settings(CONFIG_FILE)
FASTQ_VALIDATOR = CONFIG_SETTINGS['FASTQ_VALIDATOR_BINARY']
MATCH_STR = '%s*.fastq.gz' % str(args.run)
FILE_PATHS = os.path.join(args.prep_directory, MATCH_STR)
FASTQ_FILES = glob.glob(FILE_PATHS)


def execute_cmd(cmd):
    proc = subprocess.Popen(args=cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    rc = proc.wait()
    return rc


def is_valid_fastq(fastq_validator_binary, file_name):
    cmd = '%s --noeof --file %s' % (fastq_validator_binary, file_name)
    return execute_cmd(cmd)


if len(FASTQ_FILES) == 0:
    print "\nThere are not fastq files in directory\n%s\nmatching string %s\n" % (args.prep_directory, MATCH_STR)
    sys.exit(1)

for fastq_file in FASTQ_FILES:
    rc = is_valid_fastq(FASTQ_VALIDATOR, fastq_file)
    if rc != 0:
        ALL_VALID = False
        print 'This file is invalid, response code is %d:\n%s\n' % (rc, str(fastq_file))
if ALL_VALID:
    print 'All files are valid!'
