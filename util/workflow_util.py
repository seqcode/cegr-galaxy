import api_util
import json
import os
import xml_util


def get_workflow(gi, name, lh):
    lh.write('Searching for workflow named %s.\n' % name)
    workflow_info_dicts = gi.workflows.get_workflows(name=name)
    if len(workflow_info_dicts) == 0:
        return None, None
    wf_info_dict = workflow_info_dicts[0]
    workflow_id = wf_info_dict['id']
    # Get the complete workflow.
    workflow_dict = gi.workflows.show_workflow(workflow_id)
    lh.write('Found workflow named %s.\n' % name)
    return workflow_id, workflow_dict


def get_workflow_config_files(workflow_config_directory, wf_config_files_str):
    wf_config_files = wf_config_files_str.split(',')
    # Get the full path to the config_files.
    return [os.path.join(workflow_config_directory, wf_config_file) for wf_config_file in wf_config_files]


def get_workflow_input_datasets(history_name, history_input_datasets, workflow_name, workflow_dict, dbkey, lh):
    # Map the history datasets to the input datasets for the workflow.
    inputs = {}
    lh.write('\nMapping datasets from history %s to input datasets in workflow %s.\n' % (history_name, workflow_name))
    for input_index, input_dataset_dict in workflow_dict['inputs'].items():
        label = input_dataset_dict['label']
        for input_hda_name, input_hda_dict in history_input_datasets.items():
            # This requires the workflow input dataset label to be a string
            # (e.g., R1) that is contained in the name of the input dataset
            # (e.g., 60642_R1.fq).  The blacklist filter dataset must have
            # the exact label "blacklist" (without the quotes).
            if input_hda_name.find(label) >= 0 or (label == 'blacklist' and input_hda_name.find(dbkey) >= 0):
                inputs[input_index] = {'src': 'hda', 'id': input_hda_dict['id']}
                lh.write('Mapped dataset %s from history to workflow input dataset with label %s.\n' % (input_hda_name, label))
                break
    return inputs


def parse_workflow_config(wf_config_file, lh):
    if not os.path.isfile(wf_config_file):
        return None, None
    lh.write('Parsing workflow config: %s\n' % wf_config_file)
    dbkey = None
    parameters = {}
    tree = xml_util.parse_xml(wf_config_file, lh)
    root = tree.getroot()
    for elem in root:
        if elem.tag == 'dbkey':
            dbkey = elem.text
            lh.write('Found workflow dbkey: %s\n' % dbkey)
        elif elem.tag == 'parameters':
            # We're building the params dictionary
            # which must be structured as follows:
            # {STEP_ID: {NAME: VALUE, ...}
            #  STEP_ID: {NAME: VALUE, ...}}
            for step_elem in elem:
                step_id = elem.get('id', None)
                if step_id is None:
                    lh.write('Skipping tag set %s because it is missing a required id attribute.\n' % step_elem.tag)
                    continue
                for param_elem in step_elem:
                    name = None
                    value = None
                    for nv_elem in param_elem:
                        if nv_elem.tag == 'name':
                            name = param_elem.text
                        elif nv_elem.tag == 'value':
                            value = param_elem.text
                    if name is None or value is None:
                        lh.write('Skipping tag set %s because it is missing required name/value attributes.\n' % nv_elem.tag)
                        continue
                    # Add a new entry into the parameters
                    # dictionary for the current step.
                    step_params = parameters.get(step_id, {})
                    step_params[name] = value
                    parameters[step_id] = step_params
    return dbkey, parameters


def select_workflow(gi, folder_id, workflow_names, sample, run, lh):
    """
    Select a workflow (either single or paired) based on
    the number of datasets contained in the current data
    library folder.
    """
    workflow_name = None
    # Get the number of dataset within the folder.
    folder_contents_dict = gi.folders.show_folder(folder_id)
    num_datasets = folder_contents_dict['item_count']
    if num_datasets == 1:
        workflow_name = workflow_names['SINGLE']
    elif num_datasets == 2:
        workflow_name = workflow_names['PAIRED']
    if workflow_name:
        lh.write('Selected workflow named %s for sample %s of run %s\n' % (workflow_name, sample, run))
    return workflow_name, num_datasets


def start_workflow(gi, workflow_id, workflow_name, inputs, params, history_id, lh):
    lh.write('\nExecuting workflow %s.\n' % workflow_name)
    lh.write('inputs:\n%s\n\n' % str(inputs))
    lh.write('params:\n%s\n\n' % str(params))
    workflow_invocation_dict = gi.workflows.invoke_workflow(workflow_id,
                                                            inputs=inputs,
                                                            params=params,
                                                            history_id=history_id)
    lh.write('Response from executing workflow %s:\n' % workflow_name)
    lh.write('%s\n' % str(workflow_invocation_dict))


def update_workflow_params(dbkey, workflow_dict, original_parameters, lh):
    # TODO: this is brittle because it assumes specific tool ids
    # and tool parameter names.  This approach should be eliminated
    # as soon as possible and the params should be set using only
    # the workflow config XML file produced by PEGR.
    len_files = api_util.get_config_settings(type='len_files')
    parameter_updates = {}
    name = workflow_dict['name']
    lh.write('Checking for tool parameter updates for workflow %s using dbkey %s.\n' % (name, dbkey))
    step_dicts = workflow_dict.get('steps', None)
    if step_dicts is None:
        lh.write('The workflow named %s does not include any tools, so no updates are possible.\n' % name)
        return original_parameters
    for step_id, step_dict in step_dicts.items():
        if step_id in original_parameters:
            lh.write('Step_id %s is being updated via the workflow config XML created by PEGR, so skipping it here.\n' % step_id)
            continue
        tool_id = step_dict['tool_id']
        if tool_id is None:
            continue
        lh.write('\nChecking tool id: %s\n' % tool_id)
        tool_inputs_dict = step_dict['tool_inputs']
        # Handle chromInfo entries.
        chrom_info = tool_inputs_dict.get('chromInfo', None)
        if chrom_info is not None:
            len_file_path = len_files.get(dbkey.lower(), None)
            if len_file_path is None:
                # TODO: throw an exception?
                lh.write('Cannot update chromInfo setting for dbkey %s in step_id %s because no len file exists for that dbkey.\n' % (dbkey, step_id))
            else:
                updated_step_dict = parameter_updates.get(step_id, {})
                updated_step_dict['chromInfo'] = len_file_path
                parameter_updates[step_id] = updated_step_dict
                lh.write('Updated step id %s with the following entry:\n%s\n' % (step_id, str(updated_step_dict)))
        # handle reference_source entries
        if tool_id.find('bwa_mem') > 0:
            reference_source_dict = tool_inputs_dict['reference_source']
            # Convert from flattend.
            reference_source_dict = json.loads(reference_source_dict)
            reference_source_selector = reference_source_dict['reference_source_selector']
            if reference_source_selector == 'cached':
                updated_step_dict = parameter_updates.get(step_id, {})
                # TODO: this is the Galaxy 15.10 implementation
                # and may not work with newer versions.
                updated_step_dict['reference_source|ref_file'] = dbkey
                parameter_updates[step_id] = updated_step_dict
                lh.write('Updated step id %s with the following entry:\n%s\n' % (step_id, str(updated_step_dict)))
        elif tool_id.find('Extract genomic DNA') > 0:
            # Extract genomic DNA 1
            reference_genome_cond_dict = tool_inputs_dict['reference_genome_cond']
            # Convert from flattened.
            reference_genome_cond_dict = json.loads(reference_genome_cond_dict)
            reference_genome_source = reference_genome_cond_dict['reference_genome_source']
            if reference_genome_source == 'cached':
                updated_step_dict = parameter_updates.get(step_id, {})
                # TODO: this is the Galaxy 15.10 implementation
                # and may not work with newer versions.
                updated_step_dict['reference_genome_cond|reference_genome'] = dbkey
                parameter_updates[step_id] = updated_step_dict
                lh.write('Updated step id %s with the following entry:\n%s\n' % (step_id, str(updated_step_dict)))
        elif tool_id.find('repeat_masker') > 0:
            # RepeatMasker.
            new_species_value = api_util.GENOME_SPECIES_MAP.get(dbkey, None)
            if new_species_value in [None, '?']:
                # TODO: throw an exception?
                lh.write('Cannot update species setting for dbkey %s in step_id %s because that dbkey has no mapped species value.\n' % (dbkey, step_id))
            else:
                species = tool_inputs_dict.get('species', None)
                if species is not None and species.startswith('-species'):
                    # "-species fungi"
                    updated_step_dict = parameter_updates.get(step_id, {})
                    updated_step_dict['species'] = '-species %s' % new_species_value
                    parameter_updates[step_id] = updated_step_dict
                    lh.write('Updated step id %s with the following entry:\n%s\n' % (step_id, str(updated_step_dict)))
                else:
                    lh.write('Cannot update species setting for dbkey %s in step_id %s because the tool is missing the species parameter.\n' % (dbkey, step_id))
    original_parameters.update(parameter_updates)
    return original_parameters
