
import numpy as np
import os
from . import file_io
from scipy import ndimage
from utils import params

def read_raw_data(file_path, channel_start=0, channel_end=5150, time_start_idx=0, time_end_idx=60*2000,
                  channel_num=5150, header_bytes=0, chunk_height=2*60*2000):
    assert (channel_start >= 0 and channel_end <= 5150 and (channel_end - channel_start) <= channel_num)
    assert (0 <= time_start_idx <= time_end_idx)
    data_size_in_bytes = os.path.getsize(file_path)
    real_iter_num = (data_size_in_bytes-header_bytes)/(channel_num*2*400)
    assert(np.floor(real_iter_num) == real_iter_num)
    time_end_idx = int(min(real_iter_num*400, time_end_idx))
    all_raw_data = np.zeros((0, (channel_end - channel_start)), dtype=np.int16)
    for cur_time_start_idx in range(time_start_idx, time_end_idx, chunk_height):
        offset = header_bytes + cur_time_start_idx * channel_num * 2  # np.int16 is 2 bytes
        count = min((time_end_idx - cur_time_start_idx), chunk_height) * channel_num
        # print('offset: {}, count:{}'.format(offset, count))
        raw_data = np.fromfile(file_path, np.int16, count=count, offset=offset)
        # print('read')
        if raw_data.shape[0] == 0:
            break
        raw_data = raw_data.reshape((-1, channel_num))
        raw_data = raw_data[::, channel_start:channel_end:1]
        all_raw_data = np.concatenate((all_raw_data, raw_data), axis=0)
        print('raw data shape: ', all_raw_data.shape)
    print('raw data read')
    return all_raw_data


def read_norm_power(file_path, channel_start=0, channel_end=5150, time_start_idx=0, time_end_idx=60 * 2000,
                    channel_num=5150, header_bytes=0, chunk_height=60 * 2000):
    assert (channel_start >= 0 and channel_end <= 5150 and (channel_end - channel_start) <= channel_num)
    assert (0 <= time_start_idx <= time_end_idx)
    data_size_in_bytes = os.path.getsize(file_path)
    real_iter_num = (data_size_in_bytes-header_bytes) / (channel_num * 2)
    assert (np.floor(real_iter_num) == real_iter_num)
    time_end_idx = int(min(real_iter_num, time_end_idx))
    all_raw_data = np.zeros((0, (channel_end - channel_start)), dtype=np.float32)
    if header_bytes == 25:
        h_channel_start = np.fromfile(file_path, np.uint16, count=1, offset=3)
        h_channel_end = np.fromfile(file_path, np.uint16, count=1, offset=5)
        h_channel_num = h_channel_end - h_channel_start + 1
        # print(h_channel_start)
        # print(h_channel_end)
        if h_channel_num != channel_num:
            print('Record Channel num is ' + str(h_channel_num))
            return None
    for cur_time_start_idx in range(time_start_idx, time_end_idx, chunk_height):
        offset = header_bytes + cur_time_start_idx * channel_num * 4  # np.float32 is 4 bytes
        count = min((time_end_idx - cur_time_start_idx), chunk_height) * channel_num
        raw_data = np.fromfile(file_path, np.float32, count=count, offset=offset)
        if (offset + count * 4) > data_size_in_bytes:
            raw_data = raw_data[0::1]  # ?
        raw_data = raw_data.reshape((-1, channel_num))
        raw_data = raw_data[::, channel_start:channel_end:1]
        all_raw_data = np.concatenate((all_raw_data, raw_data), axis=0)
    return all_raw_data


def read_prob_data(file_path, channel_start=0, channel_end=5150, time_start_idx=0, time_end_idx=60*2000,
                   channel_num=5150, category_num=5, category_idx=1, chunk_height=10*60*60*5):
    assert (channel_start >= 0 and channel_end <= 5150 and (channel_end - channel_start) <= channel_num)
    assert (0 <= time_start_idx <= time_end_idx)
    data_size_in_bytes = os.path.getsize(file_path)
    real_iter_num = data_size_in_bytes / (channel_num * 4 * category_num)
    assert (np.floor(real_iter_num) == real_iter_num)
    time_end_idx = int(min(real_iter_num, time_end_idx))
    all_prob_data = np.zeros((0, (channel_end - channel_start)), dtype=np.float32)
    for cur_time_start_idx in range(time_start_idx, time_end_idx, chunk_height):
        offset = cur_time_start_idx * channel_num * 4 * category_num  # np.float32 is 4 bytes
        count = min((time_end_idx - cur_time_start_idx), chunk_height) * channel_num*category_num
        prob_data = np.fromfile(file_path, np.float32, count=count, offset=offset)
        if prob_data.size == 0:
            break
        prob_data = prob_data.reshape((-1, channel_num, category_num))
        prob_data = prob_data[::, channel_start:channel_end:1, category_idx]
        all_prob_data = np.concatenate((all_prob_data, prob_data), axis=0)
        print('prob data shape: ', all_prob_data.shape)
    print('prob data read')
    return all_prob_data


def read_all_prob_data(file_path, channel_start=0, channel_end=5150, time_start_idx=0, time_end_idx=60*2000,
                   channel_num=5150, category_num=5, chunk_height=10*60*60*5):
    assert (channel_start >= 0 and channel_end <= 5150 and (channel_end - channel_start) <= channel_num)
    assert (0 <= time_start_idx <= time_end_idx)
    data_size_in_bytes = os.path.getsize(file_path)
    real_iter_num = data_size_in_bytes / (channel_num * 4 * category_num)
    assert (np.floor(real_iter_num) == real_iter_num)
    elem_num_in_data = data_size_in_bytes/4  # np.float32 is 4 bytes
    assert(round(elem_num_in_data) == elem_num_in_data)
    elem_num_in_data = round(elem_num_in_data)
    time_end_idx = int(min(real_iter_num, time_end_idx))
    all_prob_data = np.fromfile(file_path, np.float32, count=elem_num_in_data, offset=0)
    all_prob_data = all_prob_data.reshape((-1, channel_num, category_num))
    all_prob_data = all_prob_data[::, channel_start:channel_end:1, ::]
    return all_prob_data



def map_prob_data(prob_data, power_data, category_num, enable_cutter_for_exc, power_data_offset):
    # read prob data shape  -> [time:, channel_no:,activity_type ]
    prob_data_mapped = np.zeros((prob_data.shape[0], prob_data.shape[1], 3))

    if category_num == 5:
        # note: each prob layer indicates the activity prob values.
        prob_data_mapped[:, :, 0] = prob_data[:, :, 0]  # copying first prob layer
        prob_data_mapped[:, :, 1] = prob_data[:, :, 1]  # copying second prob layer

        if enable_cutter_for_exc:
            prob_data_mapped[:, :, 2] = np.sum(prob_data[:, :, 2:4], axis=2)
        else:
            prob_data_mapped[:, :, 2] = prob_data[:, :, 3]

    elif category_num == 14:
        prob_data_mapped[:, :, 0] = prob_data[:, :, 0]
        prob_data_mapped[:, :, 1] = prob_data[:, :, 1]

        if enable_cutter_for_exc:
            prob_data_mapped[:, :, 2] = np.sum(prob_data[:, :, 4:7], axis=2)
        else:
            prob_data_mapped[:, :, 2] = np.sum(prob_data[:, :, 5:7], axis=2)

    """
    to apply the AND operation between power and prob data,
    the power must be longer by 3 rows than the prob data.
    """

    if power_data.shape[0] <= prob_data.shape[0] + power_data_offset:
        power_row_num = power_data.shape[0]
        prob_data_mapped = prob_data[0:power_row_num - power_data_offset, :, :]

    return prob_data_mapped


def find_counts(prob_data_mapped, norm_power_data, act, act_start, act_end, print_every=100):
    ANALYZE_PARAMS = file_io.read_json("json_files/analyze/analyze_params.json")

    # find appropriate index to use fetch analyze params for current act.
    act_type_index = ANALYZE_PARAMS["activity_names"].index(act)
    act_indices = ANALYZE_PARAMS["activity_indices"][act_type_index]
    act_prob_threshes = ANALYZE_PARAMS["activity_prob_threshes"][act_type_index]
    act_norm_power_threshes = ANALYZE_PARAMS["activity_norm_power_threshes"][act_type_index]
    act_window_size = ANALYZE_PARAMS["activity_windows"][act_type_index]
    act_adj_num = ANALYZE_PARAMS["activity_min_adjacent_nums"][act_type_index]
    act_conv_filter = ANALYZE_PARAMS["activity_conv_filters"][act_type_index]
    act_conv_filter = np.array(act_conv_filter).reshape((1, -1, 1))
    power_data_offset = ANALYZE_PARAMS["power_data_offset"]

    """ extract section of interests """
    # extract channels which we are interest
    section_interest_norm_power = norm_power_data[:, act_start:act_end]
    # convert norm power to binary based on threshold value
    section_interest_norm_power_binary = section_interest_norm_power > act_norm_power_threshes

    # prob shape -> [time, channel_no,activity_type ]
    section_interest_prob = prob_data_mapped[:, act_start:act_end, act_indices: act_indices + 1]
    prob_data_row_num = section_interest_prob.shape[0]  # row num = time index
    prob_data_col_num = section_interest_prob.shape[1]  # column number = interested channels
    real_window_size = min(prob_data_row_num, act_window_size)
    different_prob_num = len(act_prob_threshes)
    # section_interest_prob will be used to store the results for different prob threshes
    section_interest_prob = np.tile(section_interest_prob, (1, 1, different_prob_num))


    """ binarize the prob """
    section_interest_prob_binary = section_interest_prob > np.tile(np.reshape(act_prob_threshes[::],
                                                                              (1, 1, different_prob_num)),
                                                                   (prob_data_row_num, prob_data_col_num, 1))

    section_interest_norm_power_binary = np.tile(np.expand_dims(section_interest_norm_power_binary, axis=2),
                                                 (1, 1, different_prob_num))

    """ apply AND operation """
    section_interest_power_prob_anded = (section_interest_prob_binary[::, ::, ::] &
                                         section_interest_norm_power_binary[
                                         power_data_offset:power_data_offset + prob_data_row_num, ::,
                                         ::]).astype(int)
    """ falling edge detection """
    falling_edge_bool_power_prob_anded = np.concatenate((np.zeros((1, prob_data_col_num, different_prob_num)),
                                                         section_interest_power_prob_anded[1::, :, :] - section_interest_power_prob_anded[:-1:, :, :]), axis=0)

    max_act_count_nums = np.zeros((prob_data_col_num - (2 * (len(act_conv_filter) // 2)),
                                   different_prob_num))
    kernel = np.ones((real_window_size, 1, 1))

    """ calculate the activity counts """
    if act_adj_num == 1:
        section_interest_power_prob_anded_conv_x = ndimage.convolve(section_interest_power_prob_anded,
                                                                    act_conv_filter)
        section_interest_activity_counts = ndimage.convolve(section_interest_power_prob_anded_conv_x,
                                                            kernel)
        max_act_count_nums = np.max(section_interest_activity_counts, axis=0)
    elif act_adj_num == 0:  # cur_adj_num == -1 could be specialized for this case TO DO
        section_interest_power_prob_anded_conved_x = ndimage.convolve(section_interest_power_prob_anded,
                                                                      act_conv_filter)
    else:
        falling_edge_count_nums = np.zeros_like(falling_edge_bool_power_prob_anded)
        act_count_has_started = np.zeros((1, prob_data_col_num, different_prob_num))
        prob_thresh_pass_num = np.zeros_like(act_count_has_started)
        for row_idx in range(prob_data_row_num):
            for col_idx in range(prob_data_col_num):
                for prob_idx in range(different_prob_num):
                    if falling_edge_bool_power_prob_anded[row_idx, col_idx, prob_idx] == 1:
                        act_count_has_started[0, col_idx, prob_idx] = 1
                    elif falling_edge_bool_power_prob_anded[row_idx, col_idx, prob_idx] == -1:
                        if act_adj_num == -1:
                            falling_edge_count_nums[row_idx, col_idx, prob_idx] = 1
                        else:
                            falling_edge_count_nums[row_idx, col_idx, prob_idx] = prob_thresh_pass_num[
                                                                                      0, col_idx, prob_idx] // act_adj_num

                        act_count_has_started[0, col_idx, prob_idx] = 0
                        prob_thresh_pass_num[0, col_idx, prob_idx] = 0
                        if act_count_has_started[0, col_idx, prob_idx] == 1:
                            prob_thresh_pass_num[0, col_idx, prob_idx] += 1
            if row_idx % print_every == 0:
                print('{}/{}'.format(row_idx, prob_data_row_num))
        falling_edge_count_nums_conv_x = ndimage.convolve(falling_edge_count_nums, act_conv_filter)
        section_interest_activity_counts = ndimage.convolve(falling_edge_count_nums_conv_x, kernel)
        # max act count nums -> number of falling edge of and array which is created by power^prob operation
        max_act_count_nums = np.max(section_interest_activity_counts, axis=0)  # find max on time index
    # thresh_pass_nums -> number of probs which are exceed the threshold.
    thresh_pass_nums = np.sum(section_interest_prob_binary.astype(int), axis=0)  # sum on time index

    return max_act_count_nums, thresh_pass_nums


def extract_at_header(at_full_path) -> (dict, dict):
    dict_info = {}  # extracted info will be stored here.

    at_folder_path = file_io.get_parent_folder(at_full_path)
    at_file_name = file_io.get_file_name(at_full_path)
    version_to_run = 'convert_alarm_triggered.exe'
    exe_folder_path = params.EXE_FOLDER_PATH
    command_to_run = 'cd ' + exe_folder_path + ' & ' + version_to_run + ' '
    command_to_run += at_full_path + ' ' + at_folder_path + "\\"
    err = os.system(command_to_run)
    if err == 0:
        result_txt_file_path = os.path.join(at_folder_path, at_file_name + '.txt')
        txt_content = file_io.read_lines_from_txt(result_txt_file_path)
        txt_content_keys = list(map(lambda x: x.split(':')[0], txt_content))
        txt_content_values = list(map(lambda x: float(x.split(':')[1]), txt_content))
        dict_header = dict(zip(txt_content_keys, txt_content_values))
        try:
            # create info file for at.
            start_channel = int(dict_header["start_channel_number"])
            end_channel = int(dict_header["end_channel_number"])
            dict_info['selected_channel_zones'] = [start_channel, end_channel]
            dict_info['number_of_channels_in_one_sample'] = "5150"
            dict_info["start_date"], dict_info["end_date"], dict_info["alarm_id"] = at_file_name.split('_')
            dict_info["record_date_time"] = dict_info["start_date"]
            dict_info["alarm_id"] = dict_info["alarm_id"].replace(".bin", '')  # remove extension

            """calculate alarm triggered file length in seconds."""
            start_time = at_file_name.split('_')[0]
            start_year, start_month, start_day = list(map(lambda x: int(x), start_time.split("--")[0].split("-")))
            start_hour, start_minute, start_second = list(map(lambda x: int(x), start_time.split("--")[1].split("-")))
            end_time = at_file_name.split('_')[1]
            end_year, end_month, end_day = list(map(lambda x: int(x), end_time.split("--")[0].split("-")))
            end_hour, end_minute, end_second = list(map(lambda x: int(x), end_time.split("--")[1].split("-")))

            start_timestamp = datetime.datetime(start_year, start_month, start_day, start_hour,
                                                start_minute, start_second)
            end_timestamp = datetime.datetime(end_year, end_month, end_day, end_hour, end_minute, end_second)

            time_diff_sec = end_timestamp - start_timestamp
            dict_info['record_length(sec)'] = time_diff_sec.total_seconds()
            dict_info['record_notes'] = "I'm an alarm triggered file"
        except IndexError as e:
            print(e)
            raise IndexError("Error while extracting info from alarm triggered file: " + at_full_path)

        # delete .txt file
        os.remove(result_txt_file_path)

    else:
        print('error in converting ' + at_full_path)
        raise RuntimeError("Can't run the command: " + command_to_run)

    return dict_info, dict_header


def find_time_of_day(h):
    try:
        int_hour = int(h)
    except ValueError:
        int_hour = h.split("")[1]

    if 7 <= int_hour < 12:
        return "morning"
    elif 12 <= int_hour < 18:
        return "noon"
    elif 18 <= int_hour < 23:
        return "evening"
    else:
        return "night"
