import numpy as np
import csv
import os
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
from sklearn.feature_selection import f_classif, SelectPercentile
from sklearn.svm import SVC
from utils_functions import performance_metrics, feature_metrics, iter_loadtxt, impute_missing_values, scale_values, iter_loadtxt2
from imblearn.pipeline import Pipeline, make_pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
import math
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import RandomOverSampler, SMOTE
from sklearn.preprocessing import FunctionTransformer
# from CustomImputer import CustomImputer
# from CustomStandardScaler import CustomStandardScaler


# def stability(main_path, dataset_type, sampling, sampling_timing, fs_step_name, classifier_step_name):
#     print("Loading variable names...")
#     print()
#     with open(main_path + dataset_type + '/' + sampling + '/raw_train.csv', 'r') as csvfile:
#         reader = csv.reader(csvfile, delimiter=',')
#         for row in reader:
#             variable_names = np.array(list(row))
#             break
#
#     variable_names = variable_names[1:]
#
#     num_experiments = 10
#     seeds = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
#     feature_ranking = np.zeros((len(variable_names), num_experiments))
#
#     for i in range(0, num_experiments):
#         print("Loading experiment " + str(i) + " data...")
#         print()
#         raw_train_data = np.genfromtxt(main_path + dataset_type + '/' + sampling + '/experiment_' + str(i) + '_train.csv', delimiter=',')
#         raw_train_data = raw_train_data[1:, :]
#
#         X_train = raw_train_data[:, 1:]
#         y_train = raw_train_data[:, 0]
#
#         param_grid = dict()
#
#         if fs_step_name == "anova":
#             filter = SelectPercentile(f_classif, percentile=10)
#
#         if classifier_step_name == "linear_svm":
#             C_OPTIONS = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
#
#             param_grid[classifier_step_name + '__C'] = C_OPTIONS
#
#             classifier = SVC(kernel='linear', random_state=seeds[i], probability=True, class_weight='balanced')
#         elif classifier_step_name == "rf":
#             powers = list(np.arange(1, 3.2, 0.2))
#             NUM_TREES_OPTIONS = list(map(math.floor, np.multiply(3, list(map(math.pow, [10] * len(powers), powers)))))
#
#             param_grid['rf__n_estimators'] = NUM_TREES_OPTIONS
#
#             classifier = RandomForestClassifier(oob_score=True, random_state=seeds[i], n_jobs=-1, bootstrap=True, class_weight="balanced")
#         elif classifier_step_name == "knn":
#             max_num_neighbors = 60
#
#             NUM_NEIGHBORS_OPTIONS = list(np.arange(5, max_num_neighbors, 15))
#
#             param_grid[classifier_step_name + '__n_neighbors'] = NUM_NEIGHBORS_OPTIONS
#
#             classifier = KNeighborsClassifier(n_jobs=-1)
#
#         pipe = Pipeline([(fs_step_name, filter), (classifier_step_name, classifier)])
#
#         print("Performing gridsearch...")
#         print()
#
#         pipe_gridsearch = GridSearchCV(pipe, param_grid=param_grid, n_jobs=12, scoring='f1_weighted',
#                                        cv=StratifiedKFold(n_splits=5, random_state=seeds[i]))
#         pipe_gridsearch.fit(X_train, y_train)
#
#         print("Best parameters set found on development set:")
#         print()
#         print(pipe_gridsearch.best_params_)
#         print()
#
#         selected_features = np.zeros(X_train.shape[1])
#         selected_features[pipe_gridsearch.best_estimator_.named_steps[fs_step_name].get_support()] = 1
#
#         feature_ranking[:, i] = selected_features
#
#     print("Calculating final feature ranking")
#     print()
#
#     final_ranking = np.sum(feature_ranking, axis=1)
#
#     result_files_path = os.getcwd() + '/' + fs_step_name + '/classifiers/' + classifier_step_name + '/' + sampling_timing + '/' + '/' + sampling + '/' + dataset_type
#
#     save_object(feature_ranking, result_files_path + '/feature_ranking.pkl')
#
#     features_info = np.array(list(zip(np.repeat('', len(variable_names)), np.repeat(0, len(variable_names)))),
#                              dtype=[('names', 'S120'), ('stability', '>i4')])
#     features_info['names'] = variable_names
#     features_info['stability'] = final_ranking
#
#     with open(result_files_path + '/stability_features_info.csv', 'w') as f:
#         w = csv.writer(f)
#         w.writerow(['names', 'stability'])
#         w.writerows(features_info)


def general_performance(main_path, dataset_type, dataset_sub_type, sampling, sampling_timing, fs_step_name, classifier_step_name):
    print("##### Experiment Info #####")
    print("Dataset type: ", dataset_type)
    print("Dataset sub type: ", dataset_sub_type)
    print("Sampling: ", sampling)
    print("Filter FS: ", fs_step_name)
    print("Classifier: ", classifier_step_name)
    print()

    print("Loading variable names...")
    print()
    # with open(main_path + dataset_type +   '/' + sampling + '/raw_train.csv', 'r') as csvfile:
    with open(main_path + dataset_type + '/' + dataset_sub_type + '/raw_train.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            variable_names = np.array(list(row))
            break

    variable_names = variable_names[1:]

    print("Variable names:", len(variable_names))
    print(variable_names[0])
    print()

    sampling_seeds = [123, 456, 789]

    print("Loading training experiment data...")
    print()

    # raw_train_data = np.genfromtxt(main_path + dataset_type + '/' + sampling + '/raw_train.csv', delimiter=',')
    # raw_train_data = raw_train_data[1:, :]
    #
    # X_train = raw_train_data[:, 1:]
    # y_train = raw_train_data[:, 0]
    #
    # raw_test_data = np.genfromtxt(main_path + dataset_type + '/' + sampling + '/raw_test.csv', delimiter=',')
    # raw_test_data = raw_test_data[1:, :]
    #
    # X_test = raw_test_data[:, 1:]
    # y_test = raw_test_data[:, 0]

    raw_train_data = iter_loadtxt(main_path + dataset_type + '/' + dataset_sub_type + '/raw_train.csv')
    # raw_train_data = iter_loadtxt2(main_path + dataset_type + '/' + dataset_sub_type + '/raw_train.csv')
    # raw_train_data = raw_train_data[1:, :]

    # X_train = raw_train_data[:, 1:]
    # y_train = raw_train_data[:, 0]

    print("Training data:", raw_train_data[:, 1:].shape)
    print()

    experiment_results = dict()

    param_grid = dict()

    # imputer = CustomImputer(col_splitter=343)
    # scaler = CustomStandardScaler(col_splitter=343)

    # print(variable_names[341])
    # print(variable_names[342])
    # print()

    pipe = Pipeline([("imputer", FunctionTransformer(func=impute_missing_values, validate=False, pass_y=False)),
                     ("scaler", FunctionTransformer(func=scale_values, validate=False, pass_y=False))])
    # pipe = Pipeline([("imputer", FunctionTransformer(func=impute_missing_values2, validate=False, pass_y=False))])

    # param_grid['imputer__kw_args'] = [{"col_splitter": 342}]
    # param_grid['scaler__kw_args'] = [{"col_splitter": 342}]

    if fs_step_name == "anova":
        filter = SelectPercentile(f_classif, percentile=10)

    if sampling_timing == "sampling_before_fs":
        if sampling == "down_sample":
            pipe.steps.append((sampling, RandomUnderSampler(random_state=sampling_seeds[0])))
        elif sampling == "up_sample":
            pipe.steps.append((sampling, RandomOverSampler(random_state=sampling_seeds[1])))
        elif sampling == "smote_sample":
            pipe.steps.append((sampling, SMOTE(n_jobs=-1, random_state=sampling_seeds[2])))

        pipe.steps.append((fs_step_name, filter))
    elif sampling_timing == "sampling_after_fs":
        pipe.steps.append((fs_step_name, filter))

        if sampling == "down_sample":
            pipe.steps.append((sampling, RandomUnderSampler(random_state=sampling_seeds[0])))
        elif sampling == "up_sample":
            pipe.steps.append((sampling, RandomOverSampler(random_state=sampling_seeds[1])))
        elif sampling == "smote_sample":
            pipe.steps.append((sampling, SMOTE(n_jobs=-1, random_state=sampling_seeds[2])))

    if classifier_step_name == "linear_svm":
        C_OPTIONS = [0.001, 0.01, 0.1, 1, 10, 100, 1000]

        param_grid[classifier_step_name + '__C'] = C_OPTIONS

        classifier = SVC(kernel='linear', random_state=123456, probability=True, class_weight='balanced')
    elif classifier_step_name == "rf":
        powers = list(np.arange(1, 3.2, 0.2))
        NUM_TREES_OPTIONS = list(map(math.floor, np.multiply(3, list(map(math.pow, [10] * len(powers), powers)))))

        param_grid[classifier_step_name + '__n_estimators'] = NUM_TREES_OPTIONS

        classifier = RandomForestClassifier(oob_score=True, random_state=123456, n_jobs=-1, bootstrap=True,
                                            class_weight="balanced")
    elif classifier_step_name == "knn":
        max_num_neighbors = 60

        NUM_NEIGHBORS_OPTIONS = list(np.arange(5, max_num_neighbors, 15))

        param_grid[classifier_step_name + '__n_neighbors'] = NUM_NEIGHBORS_OPTIONS

        classifier = KNeighborsClassifier(n_jobs=-1)

    pipe.steps.append((classifier_step_name, classifier))

    print("Performing gridsearch...")
    print()

    pipe_gridsearch = GridSearchCV(pipe, param_grid=param_grid, n_jobs=8, scoring='f1_weighted',
                                   cv=StratifiedKFold(n_splits=10, random_state=123456), verbose=15)
    # StratifiedShuffleSplit(n_splits=10, test_size=0.3, random_state=123456)
    pipe_gridsearch.fit(raw_train_data[:, 1:], raw_train_data[:, 0])

    cv_results = dict()
    cv_results['mean_test_score'] = pipe_gridsearch.cv_results_['mean_test_score']
    cv_results['std_test_score'] = pipe_gridsearch.cv_results_['std_test_score']
    cv_results['mean_train_score'] = pipe_gridsearch.cv_results_['mean_train_score']
    cv_results['std_train_score'] = pipe_gridsearch.cv_results_['std_train_score']
    cv_results['params'] = pipe_gridsearch.cv_results_['params']

    experiment_results['cv_results'] = cv_results

    print("Best parameters set found on development set:")
    print()
    print(pipe_gridsearch.best_params_)
    print()

    print("Loading test experiment data...")
    print()

    raw_test_data = iter_loadtxt(main_path + dataset_type + '/' + dataset_sub_type + '/raw_test.csv')
    # raw_test_data = iter_loadtxt2(main_path + dataset_type + '/' + dataset_sub_type + '/raw_test.csv')
    # raw_test_data = raw_test_data[1:, :]

    # X_test = raw_test_data[:, 1:]
    # y_test = raw_test_data[:, 0]

    print("Test data:", raw_test_data[:, 1:].shape)
    print()

    performance_metrics(experiment_results, pipe_gridsearch.best_estimator_, fs_step_name, classifier_step_name,
                        raw_train_data[:, 1:], raw_train_data[:, 0], raw_test_data[:, 1:], raw_test_data[:, 0],
                        dataset_type, variable_names, sampling, sampling_timing, dataset_sub_type)


if __name__ == '__main__':
    # disease = "lung_cancer"
    disease = "diabetes"
    # chromosome = "chr12"

    # main_path = '/home/mgvaldes/devel/MIRI/master-thesis/health-forecast-project/health-forecast/datasets/' + disease + '/' + chromosome + '/'
    # main_path = '/home/aegle/health-forecast-project/health-forecast/datasets/' + disease + '/' + chromosome + '/'
    main_path = '/home/mgvaldes/devel/MIRI/master-thesis/health-forecast-project/health-forecast/datasets/' + disease + '/'
    # main_path = '/home/aegle/health-forecast-project/health-forecast/datasets/' + disease + '/'

    # sampling_timings = ["sampling_before_fs", "sampling_after_fs"]
    sampling_timings = ["sampling_before_fs"]
    # sampling_types = ["down_sample", "up_sample", "smote_sample"]
    sampling_types = ["raw"]
    # dataset_types = ["genomic", "genomic_epidemiological"]
    dataset_types = ["genomic_epidemiological"]
    # dataset_sub_types = ["D2_vs_ND", "D2_vs_H", "D2_vs_CD2F", "PD2_vs_CD2W"]
    dataset_sub_types = ["D2_vs_H"]
    fs_step_names = ["anova"]
    # classifier_step_names = ["linear_svm", "rf", "knn"]
    classifier_step_names = ["linear_svm"]

    for fs_step_name in fs_step_names:
        fs_dir = os.getcwd() + '/' + fs_step_name

        if not os.path.exists(fs_dir):
            os.makedirs(fs_dir)

        for classifier_step_name in classifier_step_names:
            classifier_dir = fs_dir + '/classifiers/' + classifier_step_name

            if not os.path.exists(classifier_dir):
                os.makedirs(classifier_dir)

            for sampling_timing in sampling_timings:
                sampling_timing_dir = classifier_dir + '/' + sampling_timing

                if not os.path.exists(sampling_timing_dir):
                    os.makedirs(sampling_timing_dir)

                for sampling in sampling_types:
                    sampling_dir = sampling_timing_dir + '/' + sampling

                    if not os.path.exists(sampling_dir):
                        os.makedirs(sampling_dir)

                    for dataset_type in dataset_types:
                        dataset_dir = sampling_dir + '/' + dataset_type

                        if not os.path.exists(dataset_dir):
                            os.makedirs(dataset_dir)

                        for dataset_sub_type in dataset_sub_types:
                            dataset_sub_type_dir = dataset_dir + '/' + dataset_sub_type

                            if not os.path.exists(dataset_sub_type_dir):
                                os.makedirs(dataset_sub_type_dir)

                            general_performance(main_path, dataset_type, dataset_sub_type, sampling, sampling_timing, fs_step_name, classifier_step_name)
                            # feature_metrics(main_path, dataset_type, sampling, sampling_timing, fs_step_name, classifier_step_name)
                            # data = iter_loadtxt2(main_path + dataset_type + '/' + dataset_sub_type + '/raw_train.csv')
                            # print(data.shape)