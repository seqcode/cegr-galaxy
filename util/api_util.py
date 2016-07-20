#!/usr/bin/env python
"""
This script contains utility functions and default values for command line
parameters used by all of the scripts within the "Send Data to Galaxy"
processing pipeline.

If command line parameters are not used for the following defaults, then the
default values must be set appropriately for the environment within which this
pipeline is run.
"""
import datetime
import json
import os
import pipes
import shutil
import string
import subprocess
import sys
import tempfile
from ConfigParser import ConfigParser
from six.moves.urllib.request import urlopen
from time import gmtime, strftime

BUFF_SIZE = 1048576
CONFIG_FILE = '../../config/cegr_config.ini'
TODAY_STR = datetime.datetime.today().strftime('%Y-%m-%d')
ANALYSIS_PREP_LOG_FILE_NAME = '%s_analysis_prep.log' % TODAY_STR
GENOME_SPECIES_MAP = {'bosTau7': 'cow',
                      'ce10': 'elegans',
                      'dm3': 'anopheles',
                      'dm5': 'anopheles',
                      'ec2': '?',
                      'hg18': 'human',
                      'hg19': 'human',
                      'hg38': 'human',
                      'kl21': 'fungi',
                      'mm9': 'mouse',
                      'mm10': 'mouse',
                      'NC003552': '?',
                      'osaindica': 'rice',
                      'osaIRGSP': 'rice',
                      'pa01': '?',
                      'pf25': '?',
                      'rn5': 'rat',
                      'sacCer3': 'fungi',
                      'sacCer3_cegr': 'fungi',
                      'Salmonella': '?',
                      'tair10': 'arabidopsis',
                      'Xac306': '?',
                      'ycp50': '?' }


def activate_virtual_env(name):
    # Galaxy releases older than 16.01 do not necessarily use
    # virtual environments, so see how this instance is set up.
    uses_virtual_environment = asbool(get_value_or_default(None, 'USES_VIRTUAL_ENV'))
    if uses_virtual_environment:
        activate_this = get_value_or_default(None, name)
        if os.path.isfile(activate_this):
            execfile(activate_this, dict(__file__=activate_this))


def archive_file(full_path_to_file, run):
    file_path, file_name = os.path.split(full_path_to_file)
    archive_dir = os.path.join(file_path, 'archive')
    if not os.path.isdir(archive_dir):
        os.makedirs(archive_dir)
    archived_file = os.path.join(archive_dir, '%s.%s.complete' % (file_name, run))
    shutil.move(full_path_to_file, archived_file)


def asbool(value):
    return value.lower() in ['true', 'yes']


def check_run_info(line, items, lh, check, index):
    if check == 'has_required_items':
        if (len(items) >= 4 and len(items) <= 7):
            return True
        else:
            lh.write('Skipping invalid line %d, it must have between 4 and 7 strings separated by semicolons:\n' % index)
            lh.write('Here is the line:\n')
            lh.write('%s\n' % line)
            return False
    if check == 'parse':
        run = str(items[0]).strip()
        sample = str(items[1]).strip()
        indexes_str = str(items[2]).strip()
        wf_config_files = str(items[3]).strip()
        if run and sample:
            lh.write('\n\n================================================\n')
            lh.write('Processing run %s sample %s.\n' % (run, sample))
        else:
            # We need valid run and sample values to create a data library.
            lh.write('Skipping line %d for invalid run %s or invalid sample %s.\n' % (index, run, sample))
            return False, None
        if not indexes_str:
            lh.write('Skipping invalid line %d, it does not contain a required index value:\n' % index)
            lh.write('Here is the line:\n')
            lh.write('%s\n' % line)
            return False, None
        if not wf_config_files:
            lh.write('Skipping invalid line %d, it does not contain a required workflow XML file name:\n' % index)
            lh.write('Here is the line:\n')
            lh.write('%s\n' % line)
            return False, None
        if len(items) >= 5:
            ext = str(items[4]).strip()
        else:
            ext = None
        if len(items) >= 6:
            data_lib_desc = str(items[5]).strip()
        else:
            data_lib_desc = None
        if len(items) == 7:
            data_lib_syn = str(items[6]).strip()
        else:
            data_lib_syn = None
        return True, (run, sample, indexes_str, wf_config_files, ext, data_lib_desc, data_lib_syn)


def cleanup_before_exit(tmp_dir):
    """
    Remove temporary files and directories.
    """
    if tmp_dir and os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


def close_log_file(lh, script_name):
    lh.write('\n\n')
    lh.write('###############################################################################\n')
    lh.write('Script %s completed.\n' % script_name)
    lh.write('Finished at: %s\n' % get_current_time())
    lh.write('###############################################################################\n\n')
    lh.close()


def copy_local_directory_of_files(src_path, dest_path, lh):
    cmd = "cp -n -R %s %s" % (src_path, dest_path)
    rc = execute_cmd(cmd, lh)
    return rc


def copy_remote_directory_of_files(host, remote_path, local_path, lh):
    cmd = "rsync -avh %s:%s %s" % (host, remote_path, local_path)
    rc = execute_cmd(cmd, lh)
    return rc


def copy_remote_file(host, remote_path, local_path, lh):
    lh.write('Copying file\n%s\nfrom host\n%s\nto local file\n%s\n\n' % (remote_path, host, local_path))
    cmd = 'scp %s:%s %s' % (host, pipes.quote(remote_path), pipes.quote(local_path))
    proc = subprocess.Popen(args=cmd, shell=True)
    proc.wait()
    rc = proc.returncode
    lh.write('\nReturn code from copy: %d\n' % rc)
    return rc == 0


def create_script_complete_file(dir, name):
    # Create a file named the value of name with a .complete extension.
    path = os.path.join(dir, '%s.complete' % name)
    fh = open(path, 'wb')
    fh.write(get_current_time())
    fh.close()


def execute_cmd(cmd, lh):
    lh.write("\nExecuting the following command:\n%s\n" % cmd)
    tmp_dir, tmp_serr_file = get_temp_dir_and_filename()
    tmp_dir, tmp_sout_file = get_temp_dir_and_filename(tmp_dir=tmp_dir)
    serrfh = open(tmp_serr_file, 'wb')
    soutfh = open(tmp_sout_file, 'wb')
    proc = subprocess.Popen(args=cmd, stderr=serrfh, stdout=soutfh, shell=True)
    rc = proc.wait()
    serrfh.close()
    soutfh.close()
    log_results(cmd, rc, tmp_serr_file, tmp_sout_file, lh)
    cleanup_before_exit(tmp_dir)
    return rc


def exists_remote(host, path, lh):
    lh.write('Checking for existence of file\n%s\non host\n%s\n' % (path, host))
    proc = subprocess.Popen(['ssh', host, 'test -f %s' % pipes.quote(path)])
    proc.wait()
    rc = proc.returncode
    lh.write('\nReturn code from check: %d\n' % rc)
    return rc == 0


def generate_sample_sheet(cegr_run_info_file, sample_sheet_path, lh):
    current_run_dir = None
    sh = open(sample_sheet_path, 'w')
    with open(cegr_run_info_file, 'r') as fh:
        sh.write('[Data]\n')
        sh.write('SampleID,SampleName,index\n')
        index_increment = 0
        for line in fh:
            line = line.strip()
            line = line.rstrip('\n')
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
                continue
            txt_items = line.split(';')
            if not (len(txt_items) >= 4 and len(txt_items) <= 7):
                lh.write('The following line is invalid and will be skipped, it must have between 4 and 7 strings separated by semicolons.\n')
                lh.write('%s\n' % line)
                continue
            run = str(txt_items[0]).strip()
            # Eliminate leading zeros.
            try:
                run = int(run)
            except:
                lh.write('The following line is invalid and will be skipped, the run must be an integer.\n')
                lh.write('%s\n' % line)
                continue
            sample = str(txt_items[1]).strip()
            # Eliminate leading zeros.
            try:
                sample = int(sample)
            except:
                lh.write('The following line is invalid and will be skipped, the sample must be an integer.\n')
                lh.write('%s\n' % line)
                continue
            indexes_str = str(txt_items[2]).strip()
            # Here are all possible permutations of indexes_str:
            # 1. ATCACG-CGATGT,AGTAGA-TTTAGC
            # 2. CGATGTTTAGGC,TTAGGC
            # 3. TTAGGCTGACCA
            # 4. ATCACG-CGATGT
            # 5.  ATCACG-CGATGT,ACAGTGGCCAAT
            indexes = indexes_str.split(',')
            # Here are all possible permutations of indexes:
            # 1. ['ATCACG-CGATGT', 'AGTAGA-TTTAGC']
            # 2. ['CGATGTTTAGGC', 'TTAGGC']
            # 3. ['TTAGGCTGACCA']
            # 4. ['ATCACG-CGATGT']
            # 5. [' ATCACG-CGATGT', 'ACAGTGGCCAAT']
            if len(indexes) > 0:
                index_increment += 1
                for index in indexes:
                    if index.find('-') > 0:
                        # If we're handling case 1 above, this must be generated:
                        # 1,200-10708,ATCACG,CGATGT
                        # 1,200-10708,AGTAGA,TTTAGC
                        # If we're handling case 4 above, this must be generated:
                        # 4,200-10711,ATCACG,CGATGT
                        # If we're handling case 5 above, this must be generated:
                        # 5,200-10712,ATCACG,CGATGT
                        # 5,200-10712,ACAGTGGCCAAT
                        index_str = index.replace('-', ',')
                    else:
                        # If we're handling case 2 above, this must be generated:
                        # 2,200-10709,CGATGTTTAGGC
                        # 2,200-10709,TTAGGC
                        # If we're handling case 3 above, this must be generated:
                        # 3,200-10710,TTAGGCTGACCA
                        # If we're handling case 5 above, this must be generated:
                        # 5,200-10712,ATCACG,CGATGT
                        # 5,200-10712,ACAGTGGCCAAT
                        index_str = index
                    csv_items = [str(index_increment), '%d-%d' % (run, sample), index_str]
                    csv_str = ','.join(csv_items)
                    sh.write('%s\n' % csv_str)
    sh.close()


def get(url):
    try:
        return json.loads(urlopen(url).read())
    except ValueError as e:
        stop_err(str(e))


def get_config_settings(config_file=None, type='defaults'):
    # Current types: defaults, workflow_invocation, workflows
    if config_file is None:
        config_file = CONFIG_FILE
    d = {}
    config_parser = ConfigParser()
    config_parser.read(config_file)
    for key, value in config_parser.items(type):
        if type == 'defaults':
            d[string.upper(key)] = value
            log_file_dir = d.get('ANALYSIS_PREP_LOG_FILE_DIR', os.getcwd())
            d['ANALYSIS_PREP_LOG_FILE'] = os.path.join(log_file_dir, ANALYSIS_PREP_LOG_FILE_NAME)
        elif type == 'len_files':
            d[key] = value
        elif type == 'workflow_invocation':
            d[string.upper(key)] = listify(value)
        elif type == 'workflows':
            d[string.upper(key)] = value
    return d


def get_current_run_directory(cegr_run_info_file):
    current_run_dir = None
    with open(cegr_run_info_file, 'r') as fh:
        for line in fh:
            line = line.strip()
            line = line.rstrip('\n')
            if not line:
                continue
            if line.startswith('#'):
                continue
            if current_run_dir is None:
                # The first non-blank, non-comment
                # line is the full path to the directory
                # on wall-E that contains the bcl files
                # for the run being processed.  Hopefully
                # this is a valid path.  There is no way
                # to test it here.
                current_run_dir = line
                break
    fh.close()
    return current_run_dir


def get_current_time():
    return strftime('%a, %d %b %Y %H:%M:%S', gmtime())


def get_galaxy_url(config_file):
    defaults = get_config_settings(config_file, section='defaults')
    return make_url(defaults['GALAXY_API_KEY'], defaults['GALAXY_BASE_URL'])


def get_run_from_sample_sheet(sample_sheet):
    run = None
    with open(sample_sheet) as fh:
        # Example SampleSheet.csv
        # [Data]
        # SampleID,SampleName,index
        # 1,198-10674,ATCACGCGATGT
        for line in fh:
            line = line.strip()
            if line.startswith('[Data]') or line.startswith('SampleID'):
                continue
            items = line.split(",")
            # SampleID, run-PEGRsampleID
            sample = items[0]
            runsample = items[1]
            run = runsample.split('-')[0]
            break
    return run


def get_stderr_exception(tmp_err, tmp_stderr):
    tmp_stderr.close()
    """
    Return a stderr string of reasonable size.
    """
    tmp_stderr = open(tmp_err, 'rb')
    stderr_str = ''
    buffsize = BUFF_SIZE
    try:
        while True:
            stderr_str += tmp_stderr.read(buffsize)
            if not stderr_str or len(stderr_str) % buffsize != 0:
                break
    except OverflowError:
        pass
    tmp_stderr.close()
    return stderr_str


def get_temp_dir(prefix='tmp-cegr-', dir=None):
    """
    Return a temporary directory.
    """
    return tempfile.mkdtemp(prefix=prefix, dir=dir)


def get_temp_dir_and_filename(tmp_dir=None):
    """
    Return a temporary file name.
    """
    if tmp_dir is None:
        tmp_dir = get_temp_dir()
    fd, filename = tempfile.mkstemp(dir=tmp_dir)
    os.close(fd)
    return tmp_dir, filename


def get_value_or_default(value, default, is_path=False, create_dir=False):
    if value is None:
        defaults = get_config_settings(type='defaults')
        value = defaults.get(default, None)
    if is_path and value is not None:
        if create_dir:
            # Create the directory if it doesn't exist.
            if not os.path.isdir(value):
                os.makedirs(value)
        return os.path.abspath(value)
    return value


def listify(item, do_strip=True):
    """
    Make a single item a single item list, or return a list if passed a
    list.  Passing a None returns an empty list.
    """
    if not item:
        return []
    elif isinstance(item, list):
        return item
    elif isinstance(item, basestring) and item.count(','):
        if do_strip:
            return [token.strip() for token in item.split(',')]
        else:
            return item.split(',')
    else:
        return [item]


def log_results(cmd, rc, tmp_serr_file, tmp_sout_file, lh):
    if tmp_sout_file is not None:
        for line in open(tmp_sout_file):
            lh.write('%s\n' % line)
    if rc != 0:
        lh.write('\nThe command\n%s\nreturned exit code %d with the following error:\n' % (cmd, rc))
        if tmp_serr_file is not None:
            for line in open(tmp_serr_file):
                lh.write('%s\n' % line)
    lh.write('\n\n')


def make_url(api_key, url, args=None):
    """
    Adds the API Key to the URL if it's not already there.
    """
    if args is None:
        args = []
    argsep = '&'
    if '?' not in url:
        argsep = '?'
    if '?key=' not in url and '&key=' not in url:
        args.insert(0, ('key', api_key))
    return url + argsep + '&'.join(['='.join(t) for t in args])


def open_log_file(log_file, script_name):
    lh = open(log_file, 'a')
    lh.write('\n\n')
    lh.write('###############################################################################\n')
    lh.write('Processing script: %s\n' % script_name)
    lh.write('Started at: %s\n' % get_current_time())
    lh.write('###############################################################################\n\n')
    return lh


def remove_remote_file(host, path, lh):
    lh.write('Removing file\n%s\nfrom host\n%s\n\n' % (path, host))
    proc = subprocess.Popen(['ssh', host, 'rm %s' % pipes.quote(path)])
    proc.wait()
    rc = proc.returncode
    lh.write('\nReturn code from file removal: %d\n' % rc)
    return rc


def stop_err(msg):
    sys.stderr.write(msg)
    sys.exit(1)
