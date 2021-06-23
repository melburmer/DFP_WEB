# file system and database params
import os
from pathlib import Path
BASE_DIR = "D:/RECORDS"
ANALYZE_RESULTS_DIR = r"D:\ANALYZE_RESULTS"
EXE_FOLDER_PATH = Path(__file__).resolve().parent.parent / 'exe_files'

file_system_values = set()

for (_, dir_names, _) in os.walk(BASE_DIR):
    for name in dir_names:
        file_system_values.add(name)

file_system_values = list(file_system_values)

# dpu params

exe_folder_name = "exe_files"
filter_mode_on = False
filters_to_compare = [
                      '222222',
                      '622202',
                      '229202',
                      '2211222',
                     ]
