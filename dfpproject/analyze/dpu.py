
import os
from utils import file_io, params
from pathlib import Path


class Dpu:
    def __init__(self, version='DPU.0.10.29.2.exe', mode="underground"):
        self.version = version
        self.mode = mode
        self.exe_folder_path = params.EXE_FOLDER_PATH
        self.filter_mode_on = params.filter_mode_on
        self.config_params_default_path = self.exe_folder_path / Path('run_time_files/config/default/')
        self.classification_models_path = self.exe_folder_path / Path('run_time_files/classification' + f"/{mode}")
        self.n_of_run = 0  # used to count the number of dpu runs.


    def __str__(self):
        return f"dpu version: {self.version}, dpu config path: {self.config_params_default_path}, mode: {self.mode}"

    def _set_algorithm_config(self, model_id, category_num, tracker_mode_on=False, filter_id=1):
        model_folder_path = os.path.join(self.classification_models_path, f'model{model_id}')
        default_algorithm_config_path = os.path.join(self.config_params_default_path, 'dpu_default_algorithm.cfg')
        default_algorithm_config = file_io.read_json(default_algorithm_config_path)

        # set preprocessors params
        preprocessor_parameters = default_algorithm_config['PreprocessorParameters']
        preprocessor_parameters['enable_classification'] = 1

        # set classification_parameters
        classification_parameters = default_algorithm_config['ClassificationParameters']
        underground_model_parameters = classification_parameters['mode_parameters'][0]['underground']
        underground_model_parameters['feature_mean_file'] = os.path.join(model_folder_path, 'meanX.txt')
        underground_model_parameters['feature_std_file'] = os.path.join(model_folder_path, 'stdX.txt')
        underground_model_parameters['nn_graph_file_2D'] = os.path.join(model_folder_path,
                                                                        'midas_model_best_freeze2D.pb')
        underground_model_parameters['number_of_classes'] = category_num
        # 0 is human, 1 is vehicle, 2 is digging, 3 is excavator

        underground_model_parameters['activity_types'][3]['class_decision_min_act_num_required'][2] = 15  # was 40
        underground_model_parameters['activity_types'][3]['declaration_probability'][2] = 0.6  # was 0.8
        if tracker_mode_on:
            underground_model_parameters['activity_types'][0]['activity_detection_power_threshold'][2] = -25.0
            underground_model_parameters['activity_types'][2]['activity_detection_power_threshold'][2] = -60.0
            underground_model_parameters['activity_types'][3]['activity_detection_power_threshold'][2] = -60.0
        else:
            underground_model_parameters['activity_types'][0]['activity_detection_power_threshold'][2] = -20.0
            underground_model_parameters['activity_types'][2]['activity_detection_power_threshold'][2] = -10.0
            underground_model_parameters['activity_types'][3]['activity_detection_power_threshold'][2] = -10.0

        # set detection parameters
        activity_detection_parameters = default_algorithm_config['ActivityDetectionParameters']
        activity_detection_parameters['alarm_timeout_duration_in_ms'] = 60000

        # set tracker parameters
        jpda_tracker_parameters = default_algorithm_config['JPDATrackerParameters']
        jpda_tracker_parameters['vehicle_tracker_enable'] = 0

        # set freq. transform parameters
        frequency_transform_parameters = default_algorithm_config['FrequencyTransformParameters']
        frequency_transform_parameters['frequency_transform_on'] = 1 if self.filter_mode_on else 0
        filter_coeffs_path = '.\\run_time_files\\filters\\filter' + str(filter_id) + '.filt'
        frequency_transform_parameters['filter_coefficients_path'] = filter_coeffs_path
        # save the default dpu config back
        file_io.save_to_json(default_algorithm_config, default_algorithm_config_path)


    def _set_development_config(self, raw_data_file_path, channel_num, start_channel):
        dpu_development_config_path = os.path.join(self.config_params_default_path, 'dpu_default_development.cfg')
        dpu_default_development = file_io.read_json(dpu_development_config_path)
        file_data_source_parameters = dpu_default_development[
            'FileDataSourceParameters']  # assignment is like reference
        file_data_source_parameters['file_data_source_enable'] = 1
        file_data_source_parameters['file_data_source_loop'] = 0
        # set absolute data path to the process
        # convert / to \\ for dpu
        raw_data_file_path = raw_data_file_path.replace("/", "\\")
        file_data_source_parameters['file_data_source_name'] = raw_data_file_path
        file_data_source_parameters['file_data_source_number_of_channels'] = channel_num
        file_data_source_parameters['file_data_source_channel_offset'] = start_channel
        file_data_source_parameters['read_time_interval_between_windos_in_ms'] = 0
        dpu_configuration_parameters = dpu_default_development[
            'DPUOutputConfigurationParameters']  # assignment is like reference
        dpu_configuration_parameters['dump_alarms_to_file'] = 1
        dpu_configuration_parameters['dump_power_to_file'] = 1
        dpu_configuration_parameters['dump_probabilities_to_file'] = 1
        # save back
        file_io.save_to_json(dpu_default_development, dpu_development_config_path)


    def _set_performance_config(self, channel_num):
        dpu_performance_settings_config_path = os.path.join(self.config_params_default_path,
                                                            'dpu_default_performance_settings.cfg')
        dpu_default_performance_settings = file_io.read_json(dpu_performance_settings_config_path)
        performance_settings_parameters = dpu_default_performance_settings[
            'PerformanceSettingsParameters']  # assignment is like reference
        performance_settings_parameters['max_number_of_channels_to_display_on_gui'] = channel_num
        performance_settings_parameters['fiber_length_in_number_of_channels'] = channel_num
        file_io.save_to_json(dpu_default_performance_settings, dpu_performance_settings_config_path)

    def _set_recorder_config(self):
        dpu_default_recorder_config_path = os.path.join(self.config_params_default_path, 'dpu_default_recorder.cfg')
        dpu_default_recorder_config = file_io.read_json(dpu_default_recorder_config_path)
        # assignment is like reference changes apply to the dpu_default_performance_settings
        recorder_main_parameters = dpu_default_recorder_config['RecorderMainParameters']
        recorder_main_parameters['enable_rolling_recorder'] = 0
        processed_data_recorder_parameters = dpu_default_recorder_config['ProcessedDataRecorderParameters']
        processed_data_recorder_parameters['enable_rolling_waterfall_recorder'] = 0
        processed_data_recorder_parameters['enable_alarm_triggered_recorder'] = 0
        file_io.save_to_json(dpu_default_recorder_config, dpu_default_recorder_config_path)

    def set_config_params(self, raw_data_file_path, model_id, category_num, channel_num,
                          start_channel, tracker_mode_on=False, filter_id=1):

        if tracker_mode_on:
            self.version = 'DPU.0.10.29_act_tracker.exe'

        # set algorithm
        self._set_algorithm_config(model_id=model_id, category_num=category_num, tracker_mode_on=tracker_mode_on,
                                   filter_id=filter_id)

        # set development
        self._set_development_config(raw_data_file_path=raw_data_file_path, channel_num=channel_num,
                                     start_channel=start_channel)
        # set performance
        self._set_performance_config(channel_num=channel_num)
        # set recorder
        self._set_recorder_config()


    def run(self):
        self.n_of_run += 1
        command_to_run = 'C:' + '& cd ' + str(self.exe_folder_path) + '&' + self.version
        err = os.system(command_to_run)  # run dpu exe

        if err:
            print('error in command ' + command_to_run)
            return err
