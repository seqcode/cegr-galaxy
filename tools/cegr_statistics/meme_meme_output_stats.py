#!/usr/bin/env python
import argparse
import stats_util

parser = argparse.ArgumentParser()
parser.add_argument('--config_file', dest='config_file', help='stats_config.ini')
parser.add_argument('--history_id', dest='history_id', help='History id')
parser.add_argument('--history_name', dest='history_name', help='History name')
parser.add_argument('--input_html', dest='input_htmls', action='append', nargs=5, help='HTML input datasets and attributes')
parser.add_argument('--input_txt', dest='input_txts', action='append', nargs=5, help='Text input datasets and attributes')
parser.add_argument('--output', dest='output', help='Output dataset')
parser.add_argument('--tool_id', dest='tool_id', help='Tool that was executed to produce the input dataset')
parser.add_argument('--tool_parameters', dest='tool_parameters', help='Tool parameters that were set when producing the input dataset')
args = parser.parse_args()

payload = stats_util.get_base_json_dict(args.config_file, dbkey, args.history_id, args.history_name, args.tool_id, args.tool_parameters)
statistics = []
datasets = []
# Generate the statistics and datasets.
for input_html in args.input_htmls:
    file_path, hid, input_id, input_datatype, dbkey = input_html
    statistics.append({})
    datasets.append(stats_util.get_datasets(args.config_file, input_id, input_datatype))
for input_txt in args.input_txts:
    file_path, hid, input_id, input_datatype, dbkey = input_txt
    statistics.append({})
    datasets.append(stats_util.get_datasets(args.config_file, input_id, input_datatype))
payload['statistics'] = statistics
payload['datasets'] = datasets
# Send the payload to PEGR.
pegr_url = stats_util.get_pegr_url(args.config_file)
response = stats_util.submit(args.config_file, payload)
# Make sure all is well.
stats_util.check_response(pegr_url, payload, response)
# If all is well, store the results in the output.
stats_util.store_results(args.output, pegr_url, payload, response)
