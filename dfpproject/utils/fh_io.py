from utils import file_io
from utils import params
import json
import os

file_hierarchy_json_path = params.file_hierarchy_json_path
dynamic_doc_values_json_path = params.dynamic_doc_values_path



def create_new_fo_use_case_file(json_path):
    records_dir = params.BASE_DIR
    with open(json_path) as json_file:
        file_hierarchy = json.load(json_file)
        if file_hierarchy["fo_use_case"] in os.listdir(records_dir):
            print(f"{file_hierarchy['fo_use_case']} was already created.")
            return -1
        for f1 in file_hierarchy["fo_use_case"]:
            for f2 in file_hierarchy["midas_version"]:
                for f3 in file_hierarchy["project"]:
                    for f4 in file_hierarchy[f"region_{f3}"]:
                        for f5 in file_hierarchy["record_type"]:
                            for f6 in file_hierarchy["activity_type"]:
                                if f5 == "alarm_triggered" and f6 == "long":
                                    continue
                                else:
                                    try:
                                        os.makedirs(records_dir + "\\" + f1 + "\\" + f2 + "\\" + f3 + "\\" + f4 + "\\" +
                                                    f5 + "\\" + f6 + "\\",
                                                    exist_ok=True)
                                    except KeyError:
                                        # if specified keys cannot found
                                        continue


def insert_new_midas_version(new_midas_version):
    is_change = False  # used to track if new midas version is added or not.
    """update file hierarchy json files."""
    file_hierarchy_json_names = os.listdir(file_hierarchy_json_path)
    for json_name in file_hierarchy_json_names:
        json_path = file_hierarchy_json_path / json_name
        json_content = file_io.read_json(json_path)
        if new_midas_version not in json_content['midas_version']:
            json_content['midas_version'].append(new_midas_version)
            is_change = True

        else:
            print(f"The '{json_name}' file hierarchy file already contain that midas version: {new_midas_version}")

        # save json back
        file_io.save_to_json(json_content, json_path)

    if is_change:
        """update dynamic document values file"""
        json_path = dynamic_doc_values_json_path
        json_content = file_io.read_json(json_path)
        if new_midas_version not in json_content["midas_version"]:
            json_content['midas_version'].append(new_midas_version)
        # save back
        file_io.save_to_json(json_content, json_path)

        """add new midas version to the file system"""
        # run create file hierarchy script
        try:
            os.system("python create_file_hierarchy.py")
            print("New midas version is successfully added to the file hierarchy")
        except Exception as e:
            print(e)


def insert_new_project(fo_use_case, new_project, new_regions: list):
    is_changed = False  # used to track if new project is added or not.

    """update dynamic document values file"""
    dynamic_json_content = file_io.read_json(dynamic_doc_values_json_path)
    if new_project not in dynamic_json_content["project"]:
        dynamic_json_content["project"].append(new_project)
        dynamic_json_content[f"region_{new_project}"] = new_regions
    # save back
    file_io.save_to_json(dynamic_json_content, dynamic_doc_values_json_path)

    """add this new project to the file hierarchy jsons"""
    file_hierarchy_json_names = os.listdir(file_hierarchy_json_path)
    for json_name in file_hierarchy_json_names:
        if json_name == "special_data.json" or json_name == "earthquake.json":
            continue

        json_path = file_hierarchy_json_path / json_name
        json_content = file_io.read_json(json_path)
        if fo_use_case == "Add new project to the all fo_use_cases":
            is_changed = True
            json_content["project"].append(new_project)
            # create new regions
            json_content[f"region_{new_project}"] = new_regions
            # save json content back
            file_io.save_to_json(json_content, json_path)

        elif json_content["fo_use_case"][0] == fo_use_case:
            if new_project not in json_content["project"]:
                is_changed = True
                json_content["project"].append(new_project)
                # create new regions
                json_content[f"region_{new_project}"] = new_regions
                # save json content back
                file_io.save_to_json(json_content, json_path)
    if is_changed:
        # run create file hierarchy script
        try:
            os.system("python create_file_hierarchy.py")
            print("New project is successfully added to the file hierarchy")
        except Exception as e:
            raise SystemError("Error while executing create_file_hierarchy.py ")


def insert_new_region(new_region_project, new_region):
    # update both file hierarchy json files and dynamic_doc_values.json file.
    key = f"region_{new_region_project}"

    # update dynamic doc
    dynamic_doc_val = file_io.read_json(dynamic_doc_values_json_path)
    if key in dynamic_doc_val.keys():
        if new_region not in dynamic_doc_val[key]:
            dynamic_doc_val[key].append(new_region)
    # save it back
    file_io.save_to_json(dynamic_doc_val, dynamic_doc_values_json_path)

    # update file_hierarchy
    is_changed = False
    for json_name in os.listdir(file_hierarchy_json_path):
        json_path = file_hierarchy_json_path / json_name
        json_content = file_io.read_json(json_path)
        if key in json_content.keys():
            is_changed = True
            if new_region not in json_content[key]:
                json_content[key].append(new_region)
        # save it back
        file_io.save_to_json(json_content, json_path)

    # run create file hierarchy script to update files
    if is_changed:
        try:
            os.system("python create_file_hierarchy.py")
            print("New region is successfully added to the file hierarchy")
        except Exception as e:
            raise SystemError("Error while executing create_file_hierarchy.py")


def insert_new_record_type(new_record_type):
    # update dynamic doc value
    dynamic_doc_values = file_io.read_json(dynamic_doc_values_json_path)
    if new_record_type not in dynamic_doc_values["record_type"]:
        dynamic_doc_values["record_type"].append(new_record_type)

    # save it back
    file_io.save_to_json(dynamic_doc_values, dynamic_doc_values_json_path)

    # update file hierarchy
    is_changed = False
    json_names = os.listdir(file_hierarchy_json_path)
    for json_name in json_names:
        json_path = file_hierarchy_json_path / json_name
        json_content = file_io.read_json(json_path)

        if "record_type" in json_content.keys():
            if new_record_type not in json_content["record_type"]:
                json_content["record_type"].append(new_record_type)
                is_changed = True
        # save it back
        file_io.save_to_json(json_content, json_path)

    # run create file hierarchy script to update files
    if is_changed:
        try:
            os.system("python create_file_hierarchy.py")
            print("New record_type is successfully added to the file hierarchy")
        except Exception as e:
            raise SystemError("Error while executing create_file_hierarchy.py")



def insert_new_activity_type(fo_use_case, new_activity_type):
    # update dynamic_document_values
    dynamic_doc_values = file_io.read_json(dynamic_doc_values_json_path)
    key = f"activity_type_{fo_use_case}"
    if key in dynamic_doc_values.keys():
        if new_activity_type not in dynamic_doc_values[key]:
            dynamic_doc_values[key].append(new_activity_type)
    # save it back
    file_io.save_to_json(dynamic_doc_values, dynamic_doc_values_json_path)

    # update file hierarchy
    is_changed = False
    json_names = os.listdir(file_hierarchy_json_path)
    for json_name in json_names:
        if "special" in json_name:
            continue
        json_path = file_hierarchy_json_path / json_name
        json_content = file_io.read_json(json_path)
        if fo_use_case == json_content["fo_use_case"][0]:
            json_content["activity_type"].append(new_activity_type)
            is_changed = True
        # save it back
        file_io.save_to_json(json_content, json_path)

    # run create file hierarchy script to update files
    if is_changed:
        try:
            os.system("python create_file_hierarchy.py")
            print("New activity_type is successfully added to the file hierarchy")
        except Exception as e:
            print(e)
