#!/usr/bin/env python
import argparse
import stats_util

parser = argparse.ArgumentParser()
parser.add_argument('--config_file', dest='config_file', help='stats_config.ini')
parser.add_argument('--dbkey', dest='dbkey', help='Input dbkey')
parser.add_argument('--history_id', dest='history_id', help='History name')
parser.add_argument('--history_name', dest='history_name', help='History name')
parser.add_argument('--input_png', dest='input_png', help='Input dataset')
parser.add_argument('--input_png_datatype', dest='input_png_datatype', help='Input dataset datatype')
parser.add_argument('--input_png_id', dest='input_png_id', help='Encoded input_png dataset id')
parser.add_argument('--input_tabular', dest='input_tabular', help='Input dataset')
parser.add_argument('--input_tabular_datatype', dest='input_tabular_datatype', help='Input dataset datatype')
parser.add_argument('--input_tabular_id', dest='input_tabular_id', help='Encoded input_tabular dataset id')
parser.add_argument('--output', dest='output', help='Output dataset')
parser.add_argument('--tool_id', dest='tool_id', help='Tool that was executed to produce the input dataset')
parser.add_argument('--tool_parameters', dest='tool_parameters', help='Tool parameters that were set when producing the input dataset')
args = parser.parse_args()

# Initialize the payload.
payload = stats_util.get_base_json_dict(args.config_file, args.dbkey, args.history_id, args.history_name, args.tool_id, args.tool_parameters)
# Generate the statistics and datasets.
payload['statistics'] = [{}, {}]
d1 = stats_util.get_datasets(args.config_file, args.input_png_id, args.input_png_datatype)
d2 = stats_util.get_datasets(args.config_file, args.input_tabular_id, args.input_tabular_datatype)
payload['datasets'] = [d1, d2]
# Send the payload to PEGR.
pegr_url = stats_util.get_pegr_url(args.config_file)
response = stats_util.submit(args.config_file, payload)
# Make sure all is well.
stats_util.check_response(pegr_url, payload, response)
# If all is well, store the results in the output.
stats_util.store_results(args.output, pegr_url, payload, response)
