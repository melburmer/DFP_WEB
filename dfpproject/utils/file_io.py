import os
import json
from datetime import datetime
import numpy
import subprocess
from tkinter import Tk, filedialog
from utils import params

dynamic_doc_values_json_path = params.dynamic_doc_values_path



def get_parent_folder(file_path) -> str:
    parent_folder, file_name = os.path.split(file_path)
    return parent_folder


def read_json(json_path) -> dict:
    with open(json_path, ) as json_file:
        content = json.load(json_file)
    return content


def get_file_name(file_path) -> str:
    parent_folder, file_name = os.path.split(file_path)
    return file_name


def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def get_num_channel_from_info(info_file_path):
    with open(info_file_path) as json_file:
        info_file = json.load(json_file)
    # fileInfo=pd.read_json(infoFile,orient='index')
    channels = info_file['selected_channel_zones']
    try:
        start_channel = channels[0]
        channel_num = channels[1] - start_channel + 1

    except:
        try:
            start_channel = channels[0][0]
            channel_num = channels[0][1] - start_channel + 1
        except:
            start_channel = 0
            try:
                channel_num = int(info_file['number_of_channels_in_one_sample'])
            except  Exception as e:
                channel_num = int(info_file['number_of_channels_in_record'])

    return start_channel, channel_num


def read_lines_from_txt(txt_path):
    with open(txt_path) as txt_file:
        txt_content = txt_file.readlines()
        txt_content = list(map(lambda line: line.strip(), txt_content))
    return txt_content


SPACE = " "
NEWLINE = "\n"


# Changed basestring to str, and dict uses items() instead of iteritems().


def to_json(o, level=0, indent=4):
    ret = ""
    if isinstance(o, dict):
        ret += "{" + NEWLINE
        comma = ""
        for k, v in o.items():
            ret += comma
            comma = ",\n"
            ret += SPACE * indent * (level + 1)
            ret += '"' + str(k) + '":' + SPACE
            ret += to_json(v, level + 1, indent=indent)

        ret += NEWLINE + SPACE * indent * level + "}"
    elif isinstance(o, str):
        o_new = o.replace('\\', '\\\\')
        ret += '"' + o_new + '"'
    elif isinstance(o, list):
        ret += "[" + ",".join([to_json(e, level + 1, indent=indent) for e in o]) + "]"
    # Tuples are interpreted as lists
    elif isinstance(o, tuple):
        ret += "[" + ",".join(to_json(e, level + 1, indent=indent) for e in o) + "]"
    elif isinstance(o, bool):
        ret += "true" if o else "false"
    elif isinstance(o, int):
        ret += str(o)
    elif isinstance(o, float):
        ret += '%.7g' % o
    elif isinstance(o, numpy.ndarray) and numpy.issubdtype(o.dtype, numpy.integer):
        ret += "[" + ','.join(map(str, o.flatten().tolist())) + "]"
    elif isinstance(o, numpy.ndarray) and numpy.issubdtype(o.dtype, numpy.inexact):
        ret += "[" + ','.join(map(lambda x: '%.7g' % x, o.flatten().tolist())) + "]"
    elif o is None:
        ret += 'null'
    else:
        raise TypeError("Unknown type '%s' for json serialization" % str(type(o)))
    return ret


def save_to_json(dictionary, json_path, indent=4):
    with open(json_path, 'w') as fp:
        try:
            cur_dict_pretty = to_json(dictionary, indent=indent)
        except:
            cur_dict_pretty = json.dumps(dictionary, indent=indent, sort_keys=True)
        fp.write(cur_dict_pretty)


def get_datetime():
    now = datetime.now()
    dt_str = now.strftime("%d-%m-%Y--%H-%M-%S")
    return dt_str


def alter_json(f_name):
    # open vi editor to edit json content
    p = subprocess.Popen(
        [r"C:\Program Files\Git\git-bash.exe", "vi", f_name],
        cwd=os.getcwd()
    )
    p.wait()


def add_value_to_json(json_path, key, new_value):
    content = read_json(json_path)
    if key in content.keys():
        if type(content[key]) is list:
            content[key].append(new_value)
        save_to_json(content, json_path)


def replace_value_in_json(json_path, key, new_val, old_val="unknown"):
    # old_val assigned to unknown to ensure call this function without old_val argument
    content = read_json(json_path)
    if key in content.keys():
        if type(content[key]) is list and old_val != "unknown":
            content[key].append(new_val)
            content[key].remove(old_val)
        else:
            content[key] = new_val
        save_to_json(content, json_path)



def ask_file_path(extension, msg=""):
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    title = f"Please select {extension} file" + msg
    source_file_path = filedialog.askopenfilename(parent=root,
    title=title, filetype=[(f"{extension} files", f"*.{extension}")])
    return source_file_path

def ask_directory():
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    directory = filedialog.askdirectory(parent=root)
    return directory


def update_dynamic_document_values(new_file_hierarchy_json_path):
    f_hierarchy = read_json(new_file_hierarchy_json_path)
    f_hierarchy_keys = f_hierarchy.keys()
    dynamic_document_values_dict = read_json(dynamic_doc_values_json_path)
    dynamic_document_values_dict_keys = dynamic_document_values_dict.keys()
    for key in f_hierarchy_keys:
        if key in dynamic_document_values_dict_keys:
            if type(f_hierarchy[key]) is list:
                if type(dynamic_document_values_dict[key]) is list:
                    for v in f_hierarchy[key]:
                        if v not in dynamic_document_values_dict[key]:
                            dynamic_document_values_dict[key].append(v)

    # update activity type in dynamic_document_values
    fo_use_case = f_hierarchy["fo_use_case"][0]
    activity_type = f_hierarchy["activity_type"]
    new_key = f"activity_type_{fo_use_case}"
    dynamic_document_values_dict[new_key] = activity_type

    save_to_json(dynamic_document_values_dict, dynamic_doc_values_json_path)
