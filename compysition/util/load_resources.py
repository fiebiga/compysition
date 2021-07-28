import os
import sys

def load_resources(path, extensions=[], strip_extensions=True, flatten=False, suppress_errors=True):
    """
    Args:
        path:               (str) The system path of the resources dir to load
        extensions:         (list) The file extensions to load
        strip_extensions:   (bool) Whether or not to strip extensions of the loaded resources from the dict keys
        flatten:            (Default: False) (bool) Whether or not to maintain file structure in nested dictionary keys
    Returns:
        (dict) Resources in dirs and subdirs
    """

    if not isinstance(extensions, list): extensions = [extensions]
    estensions = [e.lower() for e in extensions]
    accept_all_extensions = len(extensions) == 0

    files_dict = {}

    for root, subdirs, files in os.walk(path):
        for file in files:
            try:
                name, ext = file.split(os.extsep)
            except ValueError:
                if suppress_errors:
                    sys.stderr.write("Found invalid filename '{file}' in '{root}'\n".format(file=file, root=root))
                else:
                    raise
            else:
                if not strip_extensions: name = file

                if accept_all_extensions or ext.lower() in extensions:
                    file_path = os.path.join(root, file)

                    update_dict = files_dict
                    

                    if not flatten:
                        path_arr = file_path.split(path)[1].split(os.sep)[1:]
                        for _dir in path_arr[:-1]:
                            update_dict[_dir] = update_dict.get(_dir, {})
                            update_dict = update_dict[_dir]

                    update_dict.update({name: open(file_path, 'r').read()})

    return files_dict