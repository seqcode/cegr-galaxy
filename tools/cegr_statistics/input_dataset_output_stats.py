#!/usr/bin/env python
import argparse
import stats_util

parser = argparse.ArgumentParser()
parser.add_argument('--config_file', dest='config_file', help='stats_config.ini')
parser.add_argument('--dbkey', dest='dbkey', help='Input dbkey')
parser.add_argument('--history_id', dest='history_id', help='History id')
parser.add_argument('--history_name', dest='history_name', help='History name')
parser.add_argument('--input', dest='input', help='Input dataset')
parser.add_argument('--input_datatype', dest='input_datatype', help='Input dataset datatype')
parser.add_argument('--input_id', dest='input_id', help='Encoded input dataset id')
parser.add_argument('--output', dest='output', help='Output dataset')
parser.add_argument('--tool_id', dest='tool_id', help='Tool that was executed to produce the input dataset')
parser.add_argument('--user_email', dest='user_email', help='Current user email')
args = parser.parse_args()

tool_parameters = ""
if args.tool_id == 'input_dataset_r1':
    workflow_step_id = 'input1'
elif args.tool_id == 'input_dataset_r2':
    workflow_step_id - 'input2'
# Initialize the payload.
payload = stats_util.get_base_json_dict(args.config_file, args.dbkey, args.history_id, args.history_name, args.tool_id, tool_parameters, args.user_email, workflow_step_id)
# Generate the statistics and datasets.
payload['statistics'] = [{}]
payload['datasets'] = [stats_util.get_datasets(args.config_file, args.input_id, args.input_datatype)]
# Send the payload to PEGR.
pegr_url = stats_util.get_pegr_url(args.config_file)
response = stats_util.submit(args.config_file, payload)
# Make sure all is well.
stats_util.check_response(pegr_url, payload, response)
# If all is well, store the results in the output.
stats_util.store_results(args.output, pegr_url, payload, response)
