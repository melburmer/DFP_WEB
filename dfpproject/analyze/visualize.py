
from utils import file_io
import numpy as np
import matplotlib.pyplot as plt
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def visualize_roc_curves(analysis_result_path, models_to_run, acts_to_run, test_set_models_result_path):

    ANALYZE_VIS_PARAMS = file_io.read_json("json_files\\analyze\\analyze_visualize_params.json")
    # setting some variables
    plot_style = ['r-', 'b*', 'g-', 'k*', 'm-', 'c*']
    act_keys = ANALYZE_VIS_PARAMS["act_keys"]
    acts_neigh_to_consider = ANALYZE_VIS_PARAMS["acts_neigh_to_consider"]
    act_counts_to_print = ANALYZE_VIS_PARAMS["act_counts_to_print"]
    act_thresh_to_print = ANALYZE_VIS_PARAMS["act_thresh_to_print"]

    """ process the analysis_res.info to plot """

    print('currently running ' + analysis_result_path)
    try:
        dict_models = file_io.read_json(analysis_result_path)

    except FileNotFoundError as e:
        print(e)
        return -1

    all_models_summary = {}

    for model_idx, model_id in enumerate(models_to_run):
        category_num = -1
        if model_id == 0:
            category_num = 14
        elif model_id in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20]:
            category_num = 5
        #assert (category_num == 5 or category_num == 14)

        all_act_ground_truths = {}
        all_act_max_count_nums = {}
        all_act_prob_threshes = {}

        dict_all_data = dict_models["model_"+str(model_id)]

        # calculate roc curves for each acts which are given by user to analyze.
        # for each act, analyze the data and plot a roc curve.
        for act in acts_to_run:
            act_idx = act_keys.index(act)
            keys_all_data = list(dict_all_data.keys())
            prob_threshes = dict_all_data[keys_all_data[0]][act]['prob_threshes']
            n_different_prob = len(prob_threshes)
            max_count_nums = np.zeros((0, n_different_prob))
            act_ground_truths = np.zeros((0,))

            for data_idx in range(len(dict_all_data)):
                key = keys_all_data[data_idx]
                raw_data_path = dict_all_data[key]["raw_data_path"]
                ground_truth = dict_all_data[key]['ground_truth']

                if ground_truth == "long" or ground_truth == "at" or ground_truth == "tum_saha_yurume":
                    act_count_to_consider = len(dict_all_data[key][act]['channel_indices'])  # take all channels
                else:
                    act_count_to_consider = min(acts_neigh_to_consider[act_keys.index(act)],
                                                len(dict_all_data[key][act]['channel_indices']))
                # note : act_count_to_consider is used to generate more sample to use for calculating roc curve.
                cur_act_counts = np.zeros((act_count_to_consider, n_different_prob))
                cur_act_ground_truths = np.zeros(act_count_to_consider)

                for prob_idx in range(n_different_prob):
                    prob_thresh = prob_threshes[prob_idx]
                    if ground_truth == 'long' or ground_truth == 'at' or ground_truth == 'tum_saha_yurume':
                        # take all channels
                        cur_act_counts[:, prob_idx] = dict_all_data[key][act]['prob_'+str(round(prob_thresh*100))]['max_act_count_numbers']
                    else:
                        # convolve
                        act_counts_convolved = np.convolve(dict_all_data[key][act]['prob_'+str(round(prob_thresh*100))]['max_act_count_numbers'],
                                                           np.ones(act_count_to_consider), mode='valid')

                        max_idx = np.argmax(act_counts_convolved)  # find max count
                        cur_act_counts[:, prob_idx] = dict_all_data[key][act]['prob_'+str(round(prob_thresh*100))]['max_act_count_numbers'][max_idx:max_idx+act_count_to_consider:1]
                    if ground_truth == act or (ground_truth == 'tum_saha_yurume' and act == 'human'):
                        cur_act_ground_truths = np.ones_like(cur_act_ground_truths)

                # max_count_nums.shape(act_counts_to_consider, len(probs))
                max_count_nums = np.concatenate((max_count_nums, cur_act_counts), axis=0)
                # act_ground_truths: ground truth for each channel (if act==ground_truth, gt for each channls is 1)
                # act_ground_truths.shape = (act_counts_to_consider, len(probs))
                act_ground_truths = np.concatenate((act_ground_truths, cur_act_ground_truths), axis=0)
                raw_data_file_name = file_io.get_file_name(raw_data_path)
                print('Current data file name: ' + raw_data_file_name)
                print('Current data id: {}, {}/{}'.format(data_idx, data_idx + 1, len(dict_all_data)))

            all_act_max_count_nums[act] = max_count_nums   # store each corresponding act counts.
            all_act_ground_truths[act] = act_ground_truths  # store ground truths for each activity.
            all_act_prob_threshes[act] = prob_threshes  # store prob for each activity.
            print('cur activity ' + act + ' {}/{}'.format(act_idx + 1, len(acts_to_run)))

        all_models_summary[model_id] = [all_act_max_count_nums, all_act_ground_truths, all_act_prob_threshes]
        print('Current model id ' + str(model_id) + ' {}/{}'.format(model_idx + 1, len(models_to_run)))

    """ visualize """
    print("Creating figures...")
    for act_idx in range(len(acts_to_run)):  # create figure for each act
        act = acts_to_run[act_idx]
        # Created figures will be saved under act_analysis_figures_folder_path.
        act_analysis_figures_folder_path = os.path.join(test_set_models_result_path, act)
        file_io.create_folder(act_analysis_figures_folder_path)

        # read prob threshes
        prob_threshes = all_models_summary[models_to_run[0]][2][act]
        n_different_prob = len(prob_threshes)
        for prob_idx in range(n_different_prob):
            cur_prob_thresh = prob_threshes[prob_idx]
            # gonna create figure foreach prob value.
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            cnt = 0
            for model_idx in range(len(models_to_run)):
                model_id = models_to_run[model_idx]
                max_count_nums = all_models_summary[model_id][0][act]
                act_ground_truths = all_models_summary[model_id][1][act]
                gt_num = np.sum(act_ground_truths)  # number of positive sample
                cur_prob_counts = max_count_nums[:, prob_idx]  # get the prob counts for specified prob
                sort_indices = np.argsort(cur_prob_counts)
                cur_prob_counts_sorted = cur_prob_counts[sort_indices]  # ascending order
                act_ground_truths_sorted = act_ground_truths[sort_indices]  # sort with same sort indices.
                cur_prob_counts_sorted_unique, elem_counts = np.unique(cur_prob_counts_sorted, return_counts=True)
                n_unique_count_num = len(cur_prob_counts_sorted_unique)
                tp_nums = np.zeros((n_unique_count_num, ))
                fp_nums = np.zeros((n_unique_count_num, ))
                # calculate fa rate for each count.
                for idx, count_thresh in enumerate(cur_prob_counts_sorted_unique):
                    for in_idx, cur_count in enumerate(cur_prob_counts_sorted):
                        if cur_count >= count_thresh:  # if current count exceed the count threshold
                            if act_ground_truths_sorted[in_idx] == 1:  # if gt for act is==1
                                tp_nums[idx] += 1
                            elif act_ground_truths_sorted[in_idx] == 0:
                                fp_nums[idx] += 1
                n_pos_sample = np.sum(act_ground_truths_sorted)
                n_neg_sample = len(act_ground_truths_sorted)-n_pos_sample
                print('act: ' + act + ', positive sample: {}, negative sample: {}'.format(n_pos_sample, n_neg_sample))
                if n_neg_sample == 0:  # if there aren't any negative sample
                    cur_prob_fa_rates = cur_prob_counts_sorted_unique
                else:
                    cur_prob_fa_rates = fp_nums / n_neg_sample

                label_pretext = 'model: ' + str(model_id)

                if n_pos_sample == 0:
                    cur_prob_detection_rates = np.zeros((n_unique_count_num,))
                else:
                    cur_prob_detection_rates = tp_nums / n_pos_sample
                    label_txt = label_pretext+', detection rate'
                    fig.add_trace(go.Scatter(x=cur_prob_fa_rates, y=cur_prob_detection_rates, name=label_txt, mode="lines"), secondary_y=False)
                    #ax.plot(cur_prob_fa_rates, cur_prob_detection_rates, plot_style[cnt],label=label_txt)


                cnt = 0 if cnt == len(plot_style)-1 else cnt+1

                label_txt = label_pretext + ', counts-fa rate'
                print('cur prob thresh: {}'.format(cur_prob_thresh))
                if cur_prob_thresh == act_thresh_to_print[act_keys.index(act)]:
                    cur_count_to_print = act_counts_to_print[act_keys.index(act)]
                    try:
                        count_match_idx = cur_prob_counts_sorted_unique.tolist().index(cur_count_to_print)
                        print('fa: {}, dr: {}, count: {}'.format(cur_prob_fa_rates[count_match_idx],
                                                                 cur_prob_detection_rates[count_match_idx],
                                                                 cur_prob_counts_sorted_unique[count_match_idx]))
                    except ValueError:
                        pass


                fig.add_trace(go.Scatter(x=cur_prob_counts_sorted_unique, y=cur_prob_detection_rates,
                name=label_pretext + ", count-detection rate", mode="markers"),secondary_y=True)

                #ax2.plot(cur_prob_fa_rates, cur_prob_counts_sorted_unique, plot_style[cnt], label=label_txt)

                fig.update_layout(title_text='Activity: ' + act + ', Prob Thresh: ' + str(cur_prob_thresh))
                #ax3.legend(loc='upper right')
                #ax3.set_xlabel('Activity Counts')
                #cnt = 0 if cnt == len(plot_style) - 1 else cnt + 1
                fig.update_xaxes(title_text="False Alarm Rate")
                fig.update_yaxes(title_text="Detection Rate", secondary_y=False)

                #ax.set_xlabel('False Alarm Rate')
                #ax.set_ylabel('Detection Rate')
                #ax.set_title('Activity: ' + act + ', Prob Thresh: ' + str(cur_prob_thresh))

                #if gt_num:
                    #ax.legend(loc='center right')
                fig.update_yaxes(title_text="Activity Counts", secondary_y=True)
                #ax2.set_ylabel('Activity Counts')
                #ax2.legend(loc='lower right')
                img_path = os.path.join(act_analysis_figures_folder_path,
                                        'nn_roc_curve-prob_'+str(round(cur_prob_thresh * 100))+'.png')
                #plt.tight_layout()
                #plt.savefig(img_path)
                fig.show()

                print('Current model id: ' + str(model_id) + '; {}/{}'.format(model_idx + 1, len(models_to_run)))

        print('cur act: ' + act + '; {}/{}'.format(act_idx + 1, len(acts_to_run)))
