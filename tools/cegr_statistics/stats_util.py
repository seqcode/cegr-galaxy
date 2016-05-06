import json
import os
import shlex
import string
import subprocess
import sys

from ConfigParser import ConfigParser
from six.moves.urllib.error import HTTPError
from six.moves.urllib.request import Request, urlopen


def check_samtools():
    samtools_exec = which('samtools')
    if not samtools_exec:
        stop_err('Attempting to use functionality requiring samtools, but it cannot be located on Galaxy\'s PATH.')


def get_base_json_dict(dbkey, history_name):
    d = {}
    d['genome'] = dbkey
    d['run'] = get_run_from_history_name(history_name)
    d['sample'] = get_sample_from_history_name(history_name)
    return d


def get_config_settings(config_file):
    d = {}
    config_parser = ConfigParser()
    config_parser.read(config_file)
    for key, value in config_parser.items('defaults'):
        d[string.upper(key)] = value
    return d


def get_deduplicated_uniquely_mapped_reads(file_path):
    cmd = "samtools view -f 0x43 -F 0x404 -q 5 -c %s" % file_path
    return get_reads(cmd)


def get_mapped_reads(file_path):
    cmd = "samtools view -f 0x40 -F 4 -c %s" % file_path
    return get_reads(cmd)


def get_reads(cmd):
    reads = subprocess.check_output(shlex.split(cmd))
    try:
        reads = int(reads)
    except Exception, e:
        stop_err(str(e))
    return reads


def get_run_from_history_name(history_name):
    # Example: paired_001-199-10749.001
    try:
        run = int(history_name.split('-')[1])
    except Exception, e:
        stop_err(str(e))
    return run


def get_sample_from_history_name(history_name):
    # Example: paired_001-199-10749.001
    items = history_name.split('-')
    try:
        sample = int(items[2].split('.')[0])
    except Exception, e:
        stop_err(str(e))
    return sample


def get_total_reads(file_path):
    cmd = "samtools view -f 0x40 -c %s" % file_path
    return get_reads(cmd)


def get_uniquely_mapped_reads(file_path):
    cmd = "samtools view -f 0x40 -F 4 -q 5 -c %s" % file_path
    return get_reads(cmd)


def get_url(config_file):
    defaults = get_config_settings(config_file)
    return make_url(defaults['PEGR_API_KEY'], defaults['PEGR_URL'])


def make_url(api_key, url, args=None):
    """
    Adds the API Key to the URL if it's not already there.
    """
    if args is None:
        args = []
    argsep = '&'
    if '?' not in url:
        argsep = '?'
    if '?apiKey=' not in url and '&apiKey=' not in url:
        args.insert(0, ('apiKey', api_key))
    return url + argsep + '&'.join(['='.join(t) for t in args])


def post(api_key, url, data):
    url = make_url(api_key, url)
    response = Request(url, headers={'Content-Type': 'application/json'}, data=json.dumps(data))
    return json.loads(urlopen(response).read())


def stop_err(msg):
    sys.stderr.write(msg)
    sys.exit()


def submit(config_file, data):
    """
    Sends an API POST request and acts as a generic formatter for the JSON response.
    'data' will become the JSON payload read by Galaxy.
    """
    defaults = get_config_settings(config_file)
    try:
        r = post(defaults['PEGR_API_KEY'], defaults['PEGR_URL'], data)
        return r
    except HTTPError as e:
        return 'Error. ' + str(e.read(1024))


def which(file):
    # http://stackoverflow.com/questions/5226958/which-equivalent-function-in-python
    for path in os.environ["PATH"].split(":"):
        if os.path.exists(path + "/" + file):
            return path + "/" + file
    return None
