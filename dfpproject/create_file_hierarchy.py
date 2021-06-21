# CODE PURPOSE: create file hierarchy if doesn't exists.

# used directory -> D:

import json
import os


def mk_ch_dir(d):  # create given input dir and then redirect it.
    os.mkdir(d)
    os.chdir(d)


FILE_DIR = "D:\\"

FILE_HIERARCHY_JSON_PATH = r"C:\Users\aselsan\Desktop\Dataflow_Pipeline\json\file_hierarchy"
JSON_UG_DIR = os.path.join(os.path.join(os.getcwd(), "json/file_hierarchy"), "ug.json")
JSON_FENCE_DIR = os.path.join(os.path.join(os.getcwd(), "json/file_hierarchy"), "fence.json")
JSON_RAILWAY_DIR = os.path.join(os.path.join(os.getcwd(), "json/file_hierarchy"), "railway.json")
JSON_SPECIAL_DIR = os.path.join(os.path.join(os.getcwd(), "json/file_hierarchy"), "special_data.json")
CWD = os.getcwd()
destination_dirs = os.listdir(FILE_DIR)



with open(JSON_SPECIAL_DIR) as json_file:
    special_data_hierarchy = json.load(json_file)

if "ANALYZE_RESULTS" not in destination_dirs:
    os.mkdir(os.path.join(FILE_DIR, "ANALYZE_RESULTS"))

if "RECORDS" not in destination_dirs:
    mk_ch_dir(os.path.join(FILE_DIR, "RECORDS"))

else:
    os.chdir(os.path.join(FILE_DIR, "RECORDS"))

for json_name in os.listdir(FILE_HIERARCHY_JSON_PATH):
    with open(os.path.join(FILE_HIERARCHY_JSON_PATH, json_name)) as json_file:
        hierarchy = json.load(json_file)
        if 'special' in json_name:
            for f0 in ["special_data"]:
                for f1 in special_data_hierarchy["fo_use_case"]:
                    for f2 in special_data_hierarchy["midas_version"]:
                        for f3 in special_data_hierarchy["record_type"]:
                            os.makedirs(f0 + "\\" + f1 + "\\" + f2 + "\\" + f3 + "\\", exist_ok=True)
        else:
            try:
                for f1 in hierarchy["fo_use_case"]:
                    for f2 in hierarchy["midas_version"]:
                        for f3 in hierarchy["project"]:
                            for f4 in hierarchy[f"region_{f3}"]:
                                for f5 in hierarchy["record_type"]:
                                    for f6 in hierarchy["activity_type"]:
                                        if f5 == "alarm_triggered" and f6 == "long":
                                            continue
                                        else:
                                            try:
                                                os.makedirs(f1 + "\\" + f2 + "\\" + f3 + "\\" + f4 + "\\" +
                                                            f5 + "\\" + f6 + "\\",
                                                            exist_ok=True)
                                            except KeyError:
                                                # if specified keys cannot found
                                                continue
            except KeyError as e:
                print(e)
                print("Check file_hierarchy file")
os.chdir(CWD)
