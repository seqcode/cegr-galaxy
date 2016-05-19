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
args = parser.parse_args()

# Create the payload.
payload = stats_util.get_base_json_dict(args.dbkey, args.history_name)
payload['toolId'] = args.tool_id
payload['workflowId'] = stats_util.get_workflow_id(args.config_file, args.history_name)
payload['toolCategory'] = stats_util.get_tool_category(args.config_file, args.tool_id)
payload['parameters'] = stats_util.format_tool_parameters(args.tool_parameters)
statistics_dict = {}
statistics_dict['dedupUniquelyMappedReads'] = stats_util.get_deduplicated_uniquely_mapped_reads(args.input)
statistics_dict['mappedReads'] = stats_util.get_mapped_reads(args.input)
statistics_dict['totalReads'] = stats_util.get_total_reads(args.input)
statistics_dict['uniquelyMappedReads'] = stats_util.get_uniquely_mapped_reads(args.input)
payload['statistics'] = statistics_dict
datasets_dict = {}
# TODO: finish this...
payload['datasets'] = datasets_dict

pegr_url = stats_util.get_pegr_url(args.config_file)

#response = stats_util.submit(args.config_file, payload)

with open(args.output, 'w') as fh:
    fh.write("pegr_url:\n%s\n\n" % pegr_url)
    fh.write("payload:\n%s\n\n" % json.dumps(payload))
    #fh.write("response:\n%s\n" % str(response))
    fh.close()
