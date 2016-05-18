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
parser.add_argument('--tool_id', dest='tool_id', help='Tool that was executed to produce the input dataset')
parser.add_argument('--tool_parameters', dest='tool_parameters', help='Tool parameters that were set when producing the input dataset')
parser.add_argument('--command_line', dest='command_line', help='Job command line that produced the input dataset')
args = parser.parse_args()

payload = stats_util.get_base_json_dict(args.dbkey, args.history_name)
payload['dedupUniquelyMappedReads'] = stats_util.get_deduplicated_uniquely_mapped_reads(args.input)
payload['mappedReads'] = stats_util.get_mapped_reads(args.input)
payload['totalReads'] = stats_util.get_total_reads(args.input)
payload['uniquelyMappedReads'] = stats_util.get_uniquely_mapped_reads(args.input)
payload['tool_id'] = args.tool_id
payload['tool_parameters'] = args.tool_parameters
payload['command_line'] = args.command_line
payload['workflow_id'] = stats_util.get_workflow_id(args.config_file, args.history_name)
pegr_url = stats_util.get_pegr_url(args.config_file)

#response = stats_util.submit(args.config_file, payload)

with open(args.output, 'w') as fh:
    fh.write("pegr_url:\n%s\n\n" % pegr_url)
    fh.write("payload:\n%s\n\n" % json.dumps(payload))
    #fh.write("response:\n%s\n" % str(response))
    fh.close()
