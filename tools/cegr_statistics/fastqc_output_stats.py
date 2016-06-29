#!/usr/bin/env python
import argparse
import stats_util

parser = argparse.ArgumentParser()
parser.add_argument('--config_file', dest='config_file', help='stats_config.ini')
parser.add_argument('--dbkey', dest='dbkey', help='Input dbkey')
parser.add_argument('--history_id', dest='history_id', help='History name')
parser.add_argument('--history_name', dest='history_name', help='History name')
parser.add_argument('--input_html', dest='input_html', help='Input HTML dataset')
parser.add_argument('--input_html_datatype', dest='input_html_datatype', help='Input dataset datatype')
parser.add_argument('--input_html_id', dest='input_html_id', help='Encoded input_html dataset id')
parser.add_argument('--input_txt', dest='input_txt', help='Input text dataset')
parser.add_argument('--input_txt_datatype', dest='input_txt_datatype', help='Input dataset datatype')
parser.add_argument('--input_txt_id', dest='input_txt_id', help='Encoded input_txt dataset id')
parser.add_argument('--output', dest='output', help='Output dataset')
parser.add_argument('--tool_id', dest='tool_id', help='Tool that was executed to produce the input dataset')
parser.add_argument('--tool_parameters', dest='tool_parameters', help='Tool parameters that were set when producing the input dataset')
args = parser.parse_args()

# Initialize the payload.
payload = stats_util.get_base_json_dict(args.config_file, args.dbkey, args.history_id, args.history_name, args.tool_id, args.tool_parameters)
# Generate the statistics and datasets.
payload['statistics'] = {}
d1 = stats_util.get_datasets(args.config_file, args.input_html_id, args.input_html_datatype)
d2 = stats_util.get_datasets(args.config_file, args.input_txt_id, args.input_txt_datatype)
payload['datasets'] = [d1, d2]
# Send the payload to PEGR.
pegr_url = stats_util.get_pegr_url(args.config_file)
response = stats_util.submit(args.config_file, payload)
# Make sure all is well.
stats_util.check_response(pegr_url, payload, response)
# If all is well, store the results in the output.
stats_util.store_results(args.output, pegr_url, payload, response)
