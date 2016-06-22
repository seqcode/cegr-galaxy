#!/usr/bin/env python
import argparse
import os
import stats_util

parser = argparse.ArgumentParser()
parser.add_argument('--config_file', dest='config_file', help='stats_config.ini')
parser.add_argument('--history_id', dest='history_id', help='History id')
parser.add_argument('--history_name', dest='history_name', help='History name')
parser.add_argument('--input_gff', dest='input_gffs', action='append', nargs=5, help='Input Gff datasets and attributes')
parser.add_argument('--input_xml', dest='input_xmls', action='append', nargs=5, help='Input XML datasets and attributes')
parser.add_argument('--tool_id', dest='tool_id', help='Tool that was executed to produce the input dataset')
parser.add_argument('--tool_parameters', dest='tool_parameters', help='Tool parameters that were set when producing the input dataset')
args = parser.parse_args()

os.mkdir('output_gff')
os.mkdir('output_xml')

for input in args.input_gffs:
    file_path, hid, input_id, input_datatype, dbkey = input
    output_name = os.path.join('output_gff', 'statistics_on_data_%s.txt' % hid)
    # Initialize the payload.
    payload = stats_util.get_base_json_dict(args.config_file, dbkey, args.history_id, args.history_name, args.tool_id, args.tool_parameters)
    # Generate the statistics and datasets.
    payload['statistics'] = {}
    payload['datasets'] = stats_util.get_datasets(args.config_file, input_id, input_datatype)
    # Send the payload to PEGR.
    pegr_url = stats_util.get_pegr_url(args.config_file)
    response = stats_util.submit(args.config_file, payload)
    # Make sure all is well.
    stats_util.check_response(pegr_url, payload, response)
    # If all is well, store the results in the output.
    stats_util.store_results(output_name, pegr_url, payload, response)
for input in args.input_xmls:
    file_path, hid, input_id, input_datatype, dbkey = input
    output_name = os.path.join('output_xml', 'statistics_on_data_%s.txt' % hid)
    # Initialize the payload.
    payload = stats_util.get_base_json_dict(args.config_file, dbkey, args.history_id, args.history_name, args.tool_id, args.tool_parameters)
    # Generate the statistics and datasets.
    payload['statistics'] = {}
    payload['datasets'] = stats_util.get_datasets(args.config_file, input_id, input_datatype)
    # Send the payload to PEGR.
    pegr_url = stats_util.get_pegr_url(args.config_file)
    response = stats_util.submit(args.config_file, payload)
    # Make sure all is well.
    stats_util.check_response(pegr_url, payload, response)
    # If all is well, store the results in the output.
    stats_util.store_results(output_name, pegr_url, payload, response)
