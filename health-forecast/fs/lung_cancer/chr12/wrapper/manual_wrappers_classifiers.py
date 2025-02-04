import numpy as np
import csv
import os
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import SVC
from utils_functions import save_object, manual_performance_metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from ReliefF import ReliefF
from sklearn.metrics import f1_score
import math


def stability(main_path, dataset_type, sampling, sampling_timing, fs_step_name, classifier_step_name):
    print("Loading variable names...")
    print()
    with open(main_path + dataset_type + '/' + sampling + '/raw_train.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            variable_names = np.array(list(row))
            break

    variable_names = variable_names[1:]

    num_experiments = 10
    feature_ranking = np.zeros((len(variable_names), num_experiments))

    for i in range(0, num_experiments):
        print("Loading experiment " + str(i) + " data...")
        print()
        raw_train_data = np.genfromtxt(main_path + dataset_type + '/' + sampling + '/experiment_' + str(i) + '_train.csv', delimiter=',')
        raw_train_data = raw_train_data[1:, :]

        X_train = raw_train_data[:, 1:]
        y_train = raw_train_data[:, 0]

        wrapper = ReliefF(n_neighbors=50, n_features_to_keep=2000)
        wrapper.fit(X_train, y_train)

        selected_features = np.zeros(X_train.shape[1])
        selected_features[wrapper.top_features[:2000]] = 1

        feature_ranking[:, i] = selected_features

    print("Calculating final feature ranking")
    print()

    final_ranking = np.sum(feature_ranking, axis=1)

    result_files_path = os.getcwd() + '/' + fs_step_name + '/classifiers/' + classifier_step_name + '/' + sampling_timing + '/' + '/' + sampling + '/' + dataset_type

    save_object(feature_ranking, result_files_path + '/feature_ranking.pkl')

    features_info = np.array(list(zip(np.repeat('', len(variable_names)), np.repeat(0, len(variable_names)))),
                             dtype=[('names', 'S120'), ('stability', '>i4')])
    features_info['names'] = variable_names
    features_info['stability'] = final_ranking

    with open(result_files_path + '/stability_features_info.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow(['names', 'stability'])
        w.writerows(features_info)


def general_performance(main_path, dataset_type, sampling, sampling_timing, fs_step_name, classifier_step_name):
    print("Loading variable names...")
    print()
    with open(main_path + dataset_type + '/' + sampling + '/raw_train.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            variable_names = np.array(list(row))
            break

    variable_names = variable_names[1:]

    print("Loading experiment data...")
    print()
    raw_train_data = np.genfromtxt(main_path + dataset_type + '/' + sampling + '/raw_train.csv', delimiter=',')
    raw_train_data = raw_train_data[1:, :]

    X_train = raw_train_data[:, 1:]
    y_train = raw_train_data[:, 0]

    raw_test_data = np.genfromtxt(main_path + dataset_type + '/' + sampling + '/raw_test.csv', delimiter=',')
    raw_test_data = raw_test_data[1:, :]

    X_test = raw_test_data[:, 1:]
    y_test = raw_test_data[:, 0]

    experiment_results = dict()

    print("Performing gridsearch...")
    print()

    kfold = StratifiedKFold(n_splits=5, random_state=123456)

    parameters = []

    if classifier_step_name == "linear_svm":
        C_OPTIONS = [0.001, 0.01, 0.1, 1, 10, 100, 1000]

        parameters = C_OPTIONS
    elif classifier_step_name == "rf":
        powers = list(np.arange(1, 3.2, 0.2))
        NUM_TREES_OPTIONS = list(map(math.floor, np.multiply(3, list(map(math.pow, [10] * len(powers), powers)))))

        parameters = NUM_TREES_OPTIONS
    elif classifier_step_name == "knn":
        max_num_neighbors = 60
        NUM_NEIGHBORS_OPTIONS = list(np.arange(5, max_num_neighbors, 15))

        parameters = NUM_NEIGHBORS_OPTIONS

    cv_results_ = dict()
    f1_cv_results = []
    best_params_ = 0
    best_params_score_ = 0

    for param in parameters:
        print('Param: ' + str(param))

        for train_index, test_index in kfold.split(X_train, y_train):
            wrapper = ReliefF(n_neighbors=50, n_features_to_keep=2000)

            reduced_X_train = wrapper.fit_transform(X_train[train_index, :], y_train[train_index])

            if classifier_step_name == "linear_svm":
                classifier = SVC(kernel='linear', random_state=123456, probability=True, class_weight='balanced', C=param)
            elif classifier_step_name == "rf":
                classifier = RandomForestClassifier(oob_score=True, random_state=123456, n_jobs=-1, bootstrap=True,
                                                    class_weight="balanced", n_estimators=param)
            elif classifier_step_name == "knn":
                classifier = KNeighborsClassifier(n_jobs=-1, n_neighbors=param)

            classifier.fit(reduced_X_train, y_train[train_index])

            y_pred = classifier.predict(wrapper.transform(X_train[test_index, :]))

            f1_cv_results.append(f1_score(y_train[test_index], y_pred, average='weighted'))

        cv_results_[param] = {'mean_test_score': np.mean(f1_cv_results), 'std_test_score': np.std(f1_cv_results)}

        if cv_results_[param]['mean_test_score'] > best_params_score_:
            best_params_score_ = cv_results_[param]['mean_test_score']
            best_params_ = param

    experiment_results['cv_results'] = cv_results_

    print()
    print("Best parameters set found on development set:")
    print()
    print(best_params_)
    print()

    print("Constructing best estimator with best parameters:")
    print()

    wrapper = ReliefF(n_neighbors=50, n_features_to_keep=2000)

    reduced_X_train = wrapper.fit_transform(X_train, y_train)
    reduced_X_test = wrapper.transform(X_test)

    if classifier_step_name == "linear_svm":
        best_estimator_ = SVC(kernel='linear', random_state=123456, probability=True, class_weight='balanced', C=best_params_)
    elif classifier_step_name == "rf":
        best_estimator_ = RandomForestClassifier(oob_score=True, random_state=123456, n_jobs=-1, bootstrap=True,
                                            class_weight="balanced", n_estimators=best_params_)
    elif classifier_step_name == "knn":
        best_estimator_ = KNeighborsClassifier(n_jobs=-1, n_neighbors=best_params_)

    best_estimator_.fit(reduced_X_train, y_train)

    manual_performance_metrics(experiment_results, wrapper, best_estimator_, fs_step_name, classifier_step_name, reduced_X_train,
                        y_train, reduced_X_test, y_test, dataset_type, variable_names, sampling, sampling_timing)


if __name__ == '__main__':
    disease = "lung_cancer"
    chromosome = "chr12"

    main_path = '/home/mgvaldes/devel/MIRI/master-thesis/health-forecast-project/health-forecast/datasets/' + disease + '/' + chromosome + '/'
    # main_path = '/home/aegle/health-forecast-project/health-forecast/datasets/' + disease + '/' + chromosome + '/'

    sampling_timings = ["sampling_before_fs"]
    # sampling_types = ["raw", "down_sample", "up_sample", "smote_sample"]
    sampling_types = ["smote_sample"]
    # dataset_types = ["genomic", "genomic_epidemiological"]
    dataset_types = ["genomic_epidemiological"]
    fs_step_name = "relieff"
    classifier_step_name = "rf"

    classifier_dir = os.getcwd() + '/' + fs_step_name + '/classifiers/' + classifier_step_name

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

                general_performance(main_path, dataset_type, sampling, sampling_timing, fs_step_name,
                                    classifier_step_name)
            # stability(main_path, dataset_type, sampling, fs_step_name, classifier_step_name)