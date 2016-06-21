import fileinput
import json
import numpy
import os
import shlex
import string
import subprocess
import sys
import tempfile

from ConfigParser import ConfigParser
from six.moves.urllib.error import HTTPError
from six.moves.urllib.request import Request, urlopen
from six import string_types
from bioblend import galaxy


# Allows characters that are escaped to be un-escaped.
MAPPED_CHARS = {'>': '__gt__',
                '<': '__lt__',
                "'": '__sq__',
                '"': '__dq__',
                '[': '__ob__',
                ']': '__cb__',
                '{': '__oc__',
                '}': '__cc__',
                '@': '__at__',
                '\n': '__cn__',
                '\r': '__cr__',
                '\t': '__tc__',
                '#': '__pd__'}
# Maximum value of a signed 32 bit integer (2**31 - 1).
MAX_CHROM_LEN = 2147483647


def check_response(pegr_url, payload, response):
    try:
        s = json.dumps(payload)
        response_code = response.get('response_code', None)
        if response_code not in ['200']:
            err_msg = 'Error sending statistics to PEGR!\n\nPEGR URL:\n%s\n\n' % str(pegr_url)
            err_msg += 'Payload:\n%s\n\nResponse:\n%s\n' % (s, str(response))
            stop_err(err_msg)
    except Exception as e:
        err_msg = 'Error handling response from PEGR!\n\nException:\n%s\n\n' % str(e)
        err_msg += 'PEGR URL:\n%s\n\nPayload:\n%s\n\nResponse:\n%s\n' % (pegr_url, s, str(response))
        stop_err(err_msg)


def check_samtools():
    samtools_exec = which('samtools')
    if not samtools_exec:
        stop_err('Attempting to use functionality requiring samtools, but it cannot be located on Galaxy\'s PATH.')


def format_tool_parameters(parameters):
    s = parameters.lstrip('__SeP__')
    items = s.split('__SeP__')
    params = ''
    param_index = 0
    for i in range(len(items) / 2):
        param = '%s=%s' % (restore_text(items[param_index]), restore_text(items[param_index + 1]))
        params = '%s,%s' % (params, param)
        param_index += 2
    return params


def get_adapter_count(file_path):
    pass


def get_avg_insert_size(file_path):
    pass


def get_bam_file(file_path):
    pass


def get_base_json_dict(config_file, dbkey, history_id, history_name, tool_id, tool_parameters):
    d = {}
    d['genome'] = dbkey
    d['historyId'] = history_id
    d['parameters'] = format_tool_parameters(tool_parameters)
    d['run'] = get_run_from_history_name(history_name)
    d['toolCategory'] = get_tool_category(config_file, tool_id)
    d['sample'] = get_sample_from_history_name(history_name)
    d['toolId'] = tool_id
    d['workflowId'] = get_workflow_id(config_file, history_name)
    return d


def get_chrom_lengths(chrom_len_file):
    # Determine the length of each chromosome
    # and add it to the chrom_lengths dictionary.
    chrom_lengths = dict()
    len_file = fileinput.FileInput(chrom_len_file)
    try:
        for line in len_file:
            fields = line.split("\t")
            chrom_lengths[fields[0]] = int(fields[1])
    except Exception as e:
        stop_err('Error reading chromosome length file:\n%s\nException:\n%s\n' % (chrom_len_file, str(e)))
    return chrom_lengths


def get_config_settings(config_file, section='defaults'):
    d = {}
    config_parser = ConfigParser()
    config_parser.read(config_file)
    for key, value in config_parser.items(section):
        if section == 'defaults':
            d[string.upper(key)] = value
        else:
            d[key] = value
    return d


def get_datasets(config_file, ids, datatypes):
    # http://localhost:8763/datasets/eca0af6fb47bf90c/display/?preview=True
    defaults = get_config_settings(config_file, section='defaults')
    d = {}
    for i, t in zip(listify(ids), listify(datatypes)):
        d['type'] = t
        d['uri'] = '%s/datasets/%s/display?preview=True' % (defaults['GALAXY_BASE_URL'], i)
    return d


def get_deduplicated_uniquely_mapped_reads(file_path):
    cmd = "samtools view -f 0x43 -F 0x404 -q 5 -c %s" % file_path
    return get_reads(cmd)


def get_fastq_file(file_path):
    pass


def get_fastqc_report(file_path):
    pass


def get_galaxy_instance(api_key, url):
    return galaxy.GalaxyInstance(url=url, key=api_key)


def get_galaxy_url(config_file):
    defaults = get_config_settings(config_file, section='defaults')
    return make_url(defaults['GALAXY_API_KEY'], defaults['GALAXY_BASE_URL'])


def get_genome_coverage(file_path, dbkey, chrom_lengths_file):
    """
    Generate the genomce coverage for the dataset located at file_path.
    """
    lines_in_input = get_number_of_lines(file_path)
    chrom_lengths = get_chrom_lengths(chrom_lengths_file)
    chrom_length = chrom_lengths.get(dbkey, None)
    if chrom_length is None:
        # Throw an exception?
        chrom_length = MAX_CHROM_LEN
    genome_coverage = '%.4f' % float(lines_in_input / chrom_length)
    return float(genome_coverage)


def get_index_mismatch(file_path):
    pass


def get_mapped_reads(file_path):
    cmd = "samtools view -f 0x40 -F 4 -c %s" % file_path
    return get_reads(cmd)


def get_number_of_lines(file_path):
    with open(file_path) as fh:
        for i, l in enumerate(fh):
            pass
    fh.close()
    return i + 1


def get_peak_pair_wis(file_path):
    return get_number_of_lines(file_path)


def get_peak_stats(file_path):
    """
    The received file_path must point to a gff file and
    we'll return peak stats discovered in the dataset.
    """
    peak_stats = dict(numberOfPeaks=0,
                      peakMean=0,
                      peakMeanStd=0,
                      peakMedian=0,
                      peakMedianStd=0,
                      medianTagSingletons=0)
    stddevs = []
    peak_singleton_scores = []
    scores = []
    with open(file_path) as fh:
        for i, line in enumerate(fh):
            items = line.split('\t')
            # Gff column 6 is score.
            score = float(items[5])
            scores.append(score)
            # Gff column 9 is a semicolon-separated list.
            attributes = items[8].split(';')
            for attribute in attributes:
                if attribute.startswith('stddev'):
                    val = float(attribute.split('=')[1])
                    stddevs.append(val)
                    if val == 0.0:
                        # We have a peakSingleton.
                        peak_singleton_scores.append(score)
                    break
    fh.close()
    # The number of lines in the file is the number of peaks.
    peak_stats['numberOfPeaks'] = i + 1
    peak_stats['peakMean'] = numpy.mean(scores)
    peak_stats['peakMeanStd'] = numpy.mean(stddevs)
    peak_stats['peakMedian'] = numpy.median(scores)
    peak_stats['peakMedianStd'] = numpy.median(stddevs)
    peak_stats['medianTagSingletons'] = numpy.median(peak_singleton_scores)
    return peak_stats


def get_pe_histogram(file_path):
    pass


def get_pegr_url(config_file):
    defaults = get_config_settings(config_file)
    return make_url(defaults['PEGR_API_KEY'], defaults['PEGR_URL'])


def get_reads(cmd):
    try:
        reads = '%.2f' % float(subprocess.check_output(shlex.split(cmd)))
        return float(reads)
    except Exception as e:
        stop_err('Error getting reads: %s' % str(e))


def get_run_from_history_name(history_name):
    # Example: paired_001-199-10749.001
    try:
        run = int(history_name.split('-')[1])
    except Exception as e:
        stop_err('History name is likely invalid, it does not contain a run: %s' % str(e))
    return run


def get_sample_from_history_name(history_name):
    # Example: paired_001-199-10749.001
    items = history_name.split('-')
    try:
        sample = int(items[2].split('.')[0])
    except Exception as e:
        stop_err('History name is likely invalid, it does not contain a sample: %s' % str(e))
    return sample


def get_seq_duplication_level(file_path):
    pass


def get_statistics(file_path, stats, **kwd):
    # ['dedupUniquelyMappedReads', 'mappedReads', 'totalReads', 'uniquelyMappedReads']
    s = {}
    try:
        for k in stats:
            if k == 'adapterCount':
                s[k] = get_adapter_count(file_path)
            elif k == 'avgInsertSize':
                s[k] = get_avg_insert_size(file_path)
            elif k == 'bamFile':
                s[k] = get_bam_file(file_path)
            elif k == 'dedupUniquelyMappedReads':
                s[k] = get_deduplicated_uniquely_mapped_reads(file_path)
            elif k == 'fastqFile':
                s[k] = get_fastq_file(file_path)
            elif k == 'fastqcReport':
                s[k] = get_fastqc_report(file_path)
            elif k == 'genomeCoverage':
                dbkey = kwd.get('dbkey', None)
                if dbkey is None:
                    stop_err('Required dbkey parameter not received!')
                chrom_lengths_file = kwd.get('chrom_lengths_file', None)
                if chrom_lengths_file is None:
                    stop_err('Required chrom_lengths_file parameter not received!')
                s[k] = get_genome_coverage(file_path, dbkey, chrom_lengths_file)
            elif k == 'indexMismatch':
                s[k] = get_index_mismatch(file_path)
            elif k == 'mappedReads':
                s[k] = get_mapped_reads(file_path)
            elif k == 'peakPairWis':
                s[k] = get_peak_pair_wis(file_path)
            elif k == 'peakStats':
                return get_peak_stats(file_path)
            elif k == 'peHistogram':
                s[k] = get_pe_histogram(file_path)
            elif k == 'seqDuplicationLevel':
                s[k] = get_seq_duplication_level(file_path)
            elif k == 'stdDevInsertSize':
                s[k] = get_std_dev_insert_size(file_path)
            elif k == 'totalReads':
                s[k] = get_total_reads(file_path)
            elif k == 'uniquelyMappedReads':
                s[k] = get_uniquely_mapped_reads(file_path)
    except Exception as e:
        stop_err(str(e))
    return s


def get_std_dev_insert_size(file_path):
    pass


def get_tmp_filename(dir=None, suffix=None):
    fd, name = tempfile.mkstemp(suffix=suffix, dir=dir)
    os.close(fd)
    return name


def get_tool_category(config_file, tool_id):
    category_map = get_config_settings(config_file, section='tool_categories')
    return category_map.get(tool_id, 'Unknown')


def get_total_reads(file_path):
    cmd = "samtools view -f 0x40 -c %s" % file_path
    return get_reads(cmd)


def get_uniquely_mapped_reads(file_path):
    cmd = "samtools view -f 0x40 -F 4 -q 5 -c %s" % file_path
    return get_reads(cmd)


def get_workflow_id(config_file, history_name):
    workflow_name = get_workflow_name_from_history_name(history_name)
    defaults = get_config_settings(config_file)
    gi = get_galaxy_instance(defaults['GALAXY_API_KEY'], defaults['GALAXY_BASE_URL'])
    workflow_info_dicts = gi.workflows.get_workflows(name=workflow_name)
    if len(workflow_info_dicts) == 0:
        return None
    wf_info_dict = workflow_info_dicts[0]
    return wf_info_dict['id']


def get_workflow_name_from_history_name(history_name):
    # Example: paired_001-199-10749.001
    items = history_name.split('-')
    try:
        workflow_name = items[0]
    except Exception as e:
        stop_err('History name is likely invalid, it does not contain a workflow name: %s' % str(e))
    return workflow_name


def listify(item, do_strip=False):
    """
    Make a single item a single item list, or return a list if passed a
    list.  Passing a None returns an empty list.
    """
    if not item:
        return []
    elif isinstance(item, list):
        return item
    elif isinstance(item, string_types) and item.count(','):
        if do_strip:
            return [token.strip() for token in item.split(',')]
        else:
            return item.split(',')
    else:
        return [item]


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


def restore_text(text, character_map=MAPPED_CHARS):
    """Restores sanitized text"""
    if not text:
        return text
    for key, value in character_map.items():
        text = text.replace(value, key)
    return text


def stop_err(msg):
    sys.stderr.write(msg)
    sys.exit()


def store_results(file_path, pegr_url, payload, response):
    with open(file_path, 'w') as fh:
        fh.write("pegr_url:\n%s\n\n" % str(pegr_url))
        fh.write("payload:\n%s\n\n" % json.dumps(payload))
        fh.write("response:\n%s\n" % str(response))
        fh.close()


def submit(config_file, data):
    """
    Sends an API POST request and acts as a generic formatter for the JSON response.
    'data' will become the JSON payload read by Galaxy.
    """
    defaults = get_config_settings(config_file)
    try:
        return post(defaults['PEGR_API_KEY'], defaults['PEGR_URL'], data)
    except HTTPError as e:
        return json.loads(e.read())
    except Exception as e:
        return dict(response_code=None, message=e.read())


def which(file):
    # http://stackoverflow.com/questions/5226958/which-equivalent-function-in-python
    for path in os.environ["PATH"].split(":"):
        if os.path.exists(path + "/" + file):
            return path + "/" + file
    return None
