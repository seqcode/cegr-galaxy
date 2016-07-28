#!/usr/bin/env python
import argparse
import stats_util

STATS = ['peakStats']

parser = argparse.ArgumentParser()
parser.add_argument('--config_file', dest='config_file', help='stats_config.ini')
parser.add_argument('--history_id', dest='history_id', help='History id')
parser.add_argument('--history_name', dest='history_name', help='History name')
parser.add_argument('--input', dest='inputs', action='append', nargs=5, help='Input datasets and attributes')
parser.add_argument('--output', dest='output', help='Output dataset')
parser.add_argument('--tool_id', dest='tool_id', help='Tool that was executed to produce the input dataset')
parser.add_argument('--tool_parameters', dest='tool_parameters', help='Tool parameters that were set when producing the input dataset')
parser.add_argument('--workflow_step_id', dest='workflow_step_id', default=None, help='Workflow step id')
parser.add_argument('--user_email', dest='user_email', help='Current user email')
args = parser.parse_args()

payload = None
statistics = []
datasets = []
# Generate the statistics and datasets.
for input in args.inputs:
    file_path, hid, input_id, input_datatype, dbkey = input
    if payload is None:
        # Initialize the payload.
        payload = stats_util.get_base_json_dict(args.config_file, dbkey, args.history_id, args.history_name, args.tool_id, args.tool_parameters, args.user_email, args.workflow_step_id)
    statistics.append(stats_util.get_statistics(file_path, STATS))
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
