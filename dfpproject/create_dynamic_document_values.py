
import os
from utils import file_io

dynamic_doc_val_path = r"C:\Users\aselsan\Desktop\Dataflow_Pipeline\json\dynamic_document_values.json"
file_hierarchy = r"C:\Users\aselsan\Desktop\Dataflow_Pipeline\json\file_hierarchy"
records_dir = r"D:\RECORDS"

"""
find level by using directory path
for ex:
if path = "D:\\RECORDS\\underground"
len(path.split("\\")) --> gives us length 3 --> by using this number, determine the file hierarchy level
"""

# fo_use_case_level: 2
# midas version level: 3
# project level: 4
# region level: 5
#  record type level: 6
# activity type level: 7
# data level: 8

file_levels_lengths = [2, 3, 4, 5, 6, 7, 8]
file_level_names = ["fo_use_case", "midas_version", "project", "region", "record_type", "activity_type", "data"]
# map
file_level_mapped = dict(zip(file_levels_lengths, file_level_names))


# these values will created by using file hierarchy
# use set to avoid duplicate
fo_use_case_set = set()
midas_version_set = set()
project_set = set()
region_set = set()
record_type_set = set()
activity_type_set = set()

for root, _, _ in os.walk(records_dir):
    if "earthquake" in root or "special_data" in root:
        continue

    level = file_level_mapped[len(root.split("\\"))] # determine level

    if level == "fo_use_case":  # fetch all fo_use_case values
        fo_use_case_names = os.listdir(root)
        for name in fo_use_case_names:
            fo_use_case_set.add(name)

    elif level == "midas_version":  # fetch all midas_version values
        midas_version_names = os.listdir(root)
        for name in midas_version_names:
            midas_version_set.add(name)

    elif level == "project":
        project_names = os.listdir(root)
        for name in project_names:
            project_set.add(name)

    elif level == "region":  # fetch all regions with their project names
        region_project_name = root.split("\\")[-1]
        region_names = os.listdir(root)
        for region_name in region_names:
            name = region_project_name+"\\"+region_name
            region_set.add(name)

    elif level == "record_type":
        record_type_names = os.listdir(root)
        for name in record_type_names:
            record_type_set.add(name)

    elif level == "activity_type":
        #  fetch all activity_type with their fo_use_case -> because activity type value is related with the fo_use_case
        fo_use_case = root.split("\\")[2]
        activity_type_names = os.listdir(root)
        for name in activity_type_names:
            activity_type_set.add(fo_use_case+"\\"+name)

if not os.path.exists(dynamic_doc_val_path):
    # create empty dynamic_doc_val.json file.
    open(dynamic_doc_val_path, mode='a').close()
    file_io.save_to_json({}, dynamic_doc_val_path)  # init
    json_content = file_io.read_json(dynamic_doc_val_path)
    """ add fo_use_case to the dynamic document values """
    json_content["fo_use_case"] = list(fo_use_case_set)

    """ add midas_version to the dynamic document values """
    json_content["midas_version"] = list(midas_version_set)

    """ add projects to the dynamic document values """
    json_content["project"] = list(project_set)

    """ add regions to the dynamic documents set """

    regions = {}
    for val in region_set:
        project, region = val.split("\\")
        key = f"region_{project}"
        if key not in regions.keys():
            regions[key] = [region]
        else:
            regions[key].append(region)

    for key, val in regions.items():
        json_content[key] = val

    """ add record type to the dynamic document values """
    json_content["record_type"] = list(record_type_set)

    """ add activity_type to the dynamic documents set """
    activity_types = {}
    for val in activity_type_set:
        fo_use_case, act_type = val.split("\\")
        key = f"activity_type_{fo_use_case}"
        if key not in activity_types.keys():
            activity_types[key] = [act_type]
        else:
            activity_types[key].append(act_type)

    for key, val in activity_types.items():
        json_content[key] = val

    """ add soil_type to the dynamic documents set  """
    json_content["soil_type"] = ["islaktoprak", "kurutoprak", "cakil-macur", "beton", "asfalt"]

    """ add record_purpose to the dynamic documents set"""
    json_content["record_purpose"] = ["true_alarm", "false_alarm", "menhol"]

    json_content["activity_specification_human"] = ["walking", "tum_saha_yurume"]
    json_content["activity_specification_excavator"] = ["cutter"]
    file_io.save_to_json(json_content, dynamic_doc_val_path)






