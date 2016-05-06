#!/usr/bin/env python
import argparse
import json
import stats_util

stats_util.check_samtools()

parser = argparse.ArgumentParser()
parser.add_argument('--config_file', dest='config_file', help='stats_config.ini')
parser.add_argument('--input', dest='input', help='Input dataset')
parser.add_argument('--dbkey', dest='dbkey', help='Input dbkey')
parser.add_argument('--history_name', dest='history_name', help='History name')
parser.add_argument('--output', dest='output', help='Output dataset')
args = parser.parse_args()

payload = stats_util.get_base_json_dict(args.dbkey, args.history_name)
payload['dedupUniquelyMappedReads'] = stats_util.get_deduplicated_uniquely_mapped_reads(args.input)
payload['mappedReads'] = stats_util.get_mapped_reads(args.input)
payload['totalReads'] = stats_util.get_total_reads(args.input)
payload['uniquelyMappedReads'] = stats_util.get_uniquely_mapped_reads(args.input)
url = stats_util.get_url(args.config_file)

response = stats_util.submit(args.config_file, payload)

with open(args.output, 'w') as fh:
    fh.write("url:\n%s\n\n" % url)
    fh.write("payload:\n%s\n\n" % json.dumps(payload))
    fh.write("response:\n%s\n" % str(response))
    fh.close()
