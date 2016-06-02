

def add_library_dataset_to_history(gi, dbkey, history_id, history_name, dataset_id, history_input_datasets, lh):
    """
    Add a data library dataset to a history.
    """
    lh.write('\nImporting dataset id %s for dbkey %s into history %s.\n' % (dataset_id, dbkey, history_name))
    new_hda_dict = gi.histories.upload_dataset_from_library(history_id, dataset_id)
    lh.write('Response from importing dataset id %s for dbkey %s into history %s:\n' % (dataset_id, dbkey, history_name))
    lh.write('%s\n\n' % str(new_hda_dict))
    new_hda_name = new_hda_dict['name']
    history_input_datasets[new_hda_name] = new_hda_dict
    return history_input_datasets


def create_history(gi, dbkey, workflow_name, run, sample, extension, lh):
    # Create a new history to contain the analysis
    history_name = '%s-%s-%s.%s' % (workflow_name, run, sample, extension)
    new_history_dict = gi.histories.create_history(name=history_name)
    new_history_id = new_history_dict['id']
    lh.write('\nCreated a new history named %s for dbkey %s to contain the analysis for sample %s of run %s.\n' % (history_name, dbkey, sample, run))
    return history_name, new_history_id


def update_dataset(gi, dbkey, history_id, history_name, history_input_datasets, lh):
    """
    Update information about a history dataset.
    """
    for hda_name, attributes in history_input_datasets.items():
        if hda_name.find('blacklist') < 0:
            dataset_id = attributes['id']
            lh.write('\nUpdating dataset id %s for dbkey %s in history %s.\n' % (dataset_id, dbkey, history_name))
            # The response here is an HTTP response
            # (e.g., 200) when it should be a JSON dict.
            response = gi.histories.update_dataset(history_id=history_id, dataset_id=dataset_id, genome_build=dbkey)
            lh.write('Response from updating dataset id %s for dbkey %s in history %s:\n' % (dataset_id, dbkey, history_name))
            lh.write('%s\n\n' % str(response))
            # Since the call to update_dataset above unfortunately
            # returns an HTTP code, we need to request the updated
            # JSON object for the hda.
            new_hda_dict = gi.histories.show_dataset(history_id=history_id, dataset_id=dataset_id)
            lh.write('JSON dict from updating dataset id %s for dbkey %s in history %s:\n' % (dataset_id, dbkey, history_name))
            lh.write('%s\n\n' % str(new_hda_dict))
            new_hda_name = new_hda_dict['name']
            history_input_datasets[new_hda_name] = new_hda_dict
    return history_input_datasets
