import re
import os
import win32api
from helper_modules.hashing import hash_file
from database import db_class
import shutil
from decorators import timer, debug


def find_file(root, rex, extension):
    for root, dirs, files in os.walk(root):
        if ("Windows" in root) or ("$" in root) or ("Microsoft" in root):
            continue
        for f in files:
            if re.search('\\.{0}$'.format(extension), f):
                try:
                    hash_val = hash_file(os.path.join(root, f))
                except PermissionError:
                    continue
                result = rex.search(hash_val)

                if result:
                    return os.path.join(root, f)

    return "-1"


def search_file_for_all_drive(hash_val: 'hash value', extension: 'file extension') -> 'return path or -1':
    rex = re.compile(hash_val)
    for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
        found_file_path = find_file(drive, rex, extension)
        if found_file_path != -1:
            return found_file_path
        else:
            return -1


@debug
@timer
def check_queried_files(query_results) -> 'list':
    query_results.rewind()  # reset collection iterator
    results_to_return = list(query_results)
    for idx, document in enumerate(results_to_return):
        # check for bin file
        if not os.path.exists(document["data_full_path"]):
            print("Bin file can not be found in this specified path:" + document["data_full_path"])
            print("Do yuo want to search it in Pc?")
            decision = input("1:Yes,2:No")
            if decision == "1":
                # search bin file with it's hash
                hash_val = document["bin_file_hash"]
                search_result = search_file_for_all_drive(hash_val=hash_val, extension="bin")
                if search_result != -1:
                    # file is found
                    print("File is found: " + search_result)
                    print("Do you want to put it back to file hierarchy?")
                    decision = input("1: Yes, 2: No")
                    if decision == "1":
                        shutil.move(src=search_result, dst=document["data_full_path"])
                        print("Done! New destination for file: " + document["data_full_path"])
                else:
                    print("File can not be found in this pc, it'll be removed from mongo db")
                    del results_to_return[idx]

            else:
                print("File can not be found in this pc, it'll be removed from mongo db")
                input("Press any character to continue")
                # start connection
                conn = db_class.Database()
                q = {"_id": document["_id"]}
                conn.delete_document(query=q)
                conn.close_connection()
                # delete database object
                del conn
                del results_to_return[idx]

        # check for info file
        if not os.path.exists(document["data_full_path"] + ".info"):
            print("Info file can not be found in this specified path:" + document["data_full_path"] + ".info")
            print("Do yuo want to search it in Pc?")
            decision = input("1:Yes,2:No")

            if decision == "1":
                # search info file with it's hash
                hash_val = document["info_file_hash"]
                search_result = search_file_for_all_drive(hash_val=hash_val, extension="info")  # here
                if search_result != -1:
                    # file is found
                    print("File is found: " + search_result)
                    print("Do you want to put it back to file hierarchy?")
                    decision = input("1: Yes, 2: No")
                    if decision == "1":
                        shutil.move(src=search_result, dst=document["data_full_path"] + ".info")
                        print("Done! New destination for file: " + document["data_full_path"] + ".info")
                else:
                    print("File can not be found in this pc, it'll be removed from mongo db")
                    input("Press any character to continue")
                    # start connection
                    conn = db_class.Database()
                    q = {"_id": document["_id"]}
                    conn.delete_document(query=q)
                    conn.close_connection()
                    # delete object reference
                    del conn
                    del results_to_return[idx]

            else:
                del results_to_return[idx]

    return results_to_return




