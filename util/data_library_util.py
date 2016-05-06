

def get_blacklist_filter_dataset_id(gi, data_lib_id, dbkey, lh):
    """
    Use the Galaxy API to get the blacklist filter dataset for the dbkey.
    We're assuming it is in the root folder.
    """
    lh.write('Searching for blacklist filter dataset for dbkey %s.\n' % dbkey)
    lib_item_dicts = gi.libraries.show_library(data_lib_id, contents=True)
    for lib_item_dict in lib_item_dicts:
        if lib_item_dict['type'] == 'file':
            dataset_name = lib_item_dict['name'].lstrip('/').lower()
            if dataset_name.startswith(dbkey.lower()):
                # Handle the non-standard CEGR proprietary sacCer3_cegr genome.
                if dbkey.lower() == 'saccer3_cegr':
                    if not dataset_name.startswith('saccer3_cegr'):
                        continue
                if dbkey.lower() == 'saccer3':
                    if dataset_name.startswith('saccer3_cegr'):
                        continue
                lh.write('Found blacklist filter dataset for dbkey %s.\n' % dbkey)
                return lib_item_dict['id']
    return None


def get_data_library(gi, name, lh):
    """
    Use the Galaxy API to get the data library named the value name.
    """
    lh.write('Searching for data library named %s.\n' % name)
    # The following is not correctly filtering out deleted libraries.
    data_lib_dicts = gi.libraries.get_libraries(library_id=None, name=name, deleted=False)
    for data_lib_dict in data_lib_dicts:
        if data_lib_dict['name'] == name and data_lib_dict['deleted'] not in [True, 'true', 'True']:
            lh.write('Found data library named %s.\n' % name)
            return data_lib_dict['id']
    return None


def get_folder(gi, data_lib_id, data_lib_name, name, lh):
    """
    Use the Galaxxy API to get the folder named the value of name.
    """
    lh.write('Searching for folder named %s from data library %s.\n' % (name, data_lib_name))
    folder_dicts = gi.libraries.get_folders(data_lib_id, folder_id=None, name=None)
    for folder_dict in folder_dicts:
        folder_name = folder_dict['name'].lstrip('/')
        if folder_name == name:
            lh.write('Found folder named %s from data library %s.\n' % (name, data_lib_name))
            return folder_dict['id']
    return None


def get_sample_datasets(gi, data_lib_id, sample, run, lh):
    # Get the datasets from the current folder.
    lh.write('Searching for the number of datasets for sample %s of run %s.\n' % (sample, run))
    lib_input_datasets = {}
    lib_content_dicts = gi.libraries.show_library(data_lib_id, contents=True)
    for lib_content_dict in lib_content_dicts:
        if lib_content_dict['type'] == 'file':
            item_name = lib_content_dict['name'].lstrip('/')
            if item_name.startswith(sample):
                lib_input_datasets[lib_content_dict['id']] = lib_content_dict['name']
    lh.write('Found %d datasets for sample %s of run %s.\n' % (len(lib_input_datasets), sample, run))
    return lib_input_datasets
