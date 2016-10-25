import numpy as np
import csv
import os
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_selection import SelectFromModel, SelectPercentile
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix, accuracy_score, precision_recall_fscore_support
from sklearn.metrics import roc_curve, auc, f1_score
from plot_functions import plot_confusion_matrix, plot_roc
from utils_functions import save_object
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import RandomizedLogisticRegression, LassoCV

experiments_results = dict()

num_experiments = 10

seeds = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
C_OPTIONS = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
THRESHOLD_OPTIONS = [0.1]
ALPHA_OPTIONS = [0.85]

print("Loading variable names...")
print()
with open('/home/mgvaldes/devel/MIRI/master-thesis/health-forecast/raw/raw_train.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        variable_names = np.array(list(row))
        break

variable_names = variable_names[1:]

feature_ranking = np.zeros((len(variable_names), num_experiments))
F1s = []
coefficients = np.zeros((len(variable_names), num_experiments))

for i in range(0, num_experiments):
    experiment_results = dict()

    print("Loading experiment " + str(i) + " data...")
    print()
    raw_train_data = np.genfromtxt(
        '/home/mgvaldes/devel/MIRI/master-thesis/health-forecast/fs/raw/experiment_' + str(i) + '_train.csv',
        delimiter=',')
    raw_train_data = raw_train_data[1:, :]

    X_train = raw_train_data[:, 1:]
    y_train = raw_train_data[:, 0]

    raw_test_data = np.genfromtxt(
        '/home/mgvaldes/devel/MIRI/master-thesis/health-forecast/fs/raw/experiment_' + str(i) + '_test.csv',
        delimiter=',')
    raw_test_data = raw_test_data[1:, :]

    X_test = raw_test_data[:, 1:]
    y_test = raw_test_data[:, 0]

    # lasso = RandomizedLogisticRegression(random_state=seeds[i])
    #
    # lasso_embedded = SelectPercentile(lasso, percentile=10)
    #
    # linear_svm = SVC(kernel='linear', random_state=seeds[i], probability=True, class_weight='balanced')
    #
    # lasso_linear_svm_pipe = Pipeline([('lasso', lasso_embedded), ('linear_svm', linear_svm)])
    #
    # param_grid = {
    #     # 'lasso__threshold': THRESHOLD_OPTIONS,
    #     # 'lasso__alpha': ALPHA_OPTIONS,
    #     'linear_svm__C': C_OPTIONS
    # }
    #
    # skf = StratifiedKFold(n_splits=5, random_state=seeds[i])
    #
    # linear_svm_gridsearch = GridSearchCV(lasso_linear_svm_pipe, param_grid=param_grid, cv=skf, scoring='f1_weighted')
    #
    # print("Performing automatic gridsearch over C parameter, including feature selection over each fold")
    # print()
    # linear_svm_gridsearch.fit(X_train, y_train)

    skf = StratifiedKFold(n_splits=5, random_state=seeds[i])

    C_gridsearch_results = dict()
    print("Performing manual gridsearch over C parameter")
    print()

    for C in C_OPTIONS:
        print("####################### CV for C = " + str(C))
        print()
        j = 0
        F1s = []

        for train_index, test_index in skf.split(X_train, y_train):
            print("Working over fold " + str(j) + ":")
            print()
            print("Performing FS over fold " + str(j))
            print()
            # Perform FS
            lasso = RandomizedLogisticRegression(random_state=seeds[i], selection_threshold=0.1)
            lasso.fit(X_train[train_index, :], y_train[train_index])

            print("Transforming X_train of fold " + str(j) + " with selected features")
            print()
            # Use only selected features of training set
            reduced_X_train = lasso.transform(X_train[train_index, :])

            print("Selected " + str(reduced_X_train.shape[1]) + " features")
            print()

            linear_svm = SVC(kernel='linear', random_state=seeds[i], probability=True, class_weight='balanced')
            print("Training SVC with reduced X_train of fold " + str(j))
            print()
            linear_svm.fit(reduced_X_train, y_train[train_index])

            print("Predicting y_test of fold " + str(j) + " with reduced X_test of fold " + str(j))
            print()
            # Use only selected features of test set
            y_pred = linear_svm.predict((X_train[test_index, :])[:, lasso.get_support()])

            F1s.append(f1_score(y_train[test_index], y_pred, average='weighted'))

            j += 1

        C_gridsearch_results[C] = np.mean(np.array(F1s))

    print("Best C parameter: ")
    best_C = list(C_gridsearch_results.keys())[
        list(C_gridsearch_results.values()).index(max(list(C_gridsearch_results.values())))]
    print(best_C)
    print()

    lasso = RandomizedLogisticRegression(random_state=seeds[i], selection_threshold=0.1)
    lasso.fit(X_train, y_train)

    linear_svm = SVC(kernel='linear', random_state=seeds[i], probability=True, class_weight='balanced', C=best_C)

    experiment_results['fs'] = lasso

    selected_features = np.zeros(X_train.shape[1])
    selected_features[lasso.get_support()] = 1

    feature_ranking[:, i] = selected_features

    linear_svm.fit(X_train[:, lasso.get_support()], y_train)

    experiment_results['model'] = linear_svm

    linear_svm_coefficients = np.zeros(X_train.shape[1])
    linear_svm_coefficients[lasso.get_support()] = np.absolute(linear_svm.coef_)

    coefficients[:, i] = linear_svm_coefficients

    print("Predicting y_test with reduced X_test")
    print()
    # Use only selected features of test set
    y_pred = linear_svm.predict(X_test[:, lasso.get_support()])

    print("Probabilities:")
    y_prob = linear_svm.predict_proba(X_test[:, lasso.get_support()])
    experiment_results['y_prob'] = y_prob
    print(y_prob)
    print()

    print()
    print("Accuracy:")
    linear_svm_accuracy = accuracy_score(y_test, y_pred)
    experiment_results['accuracy'] = linear_svm_accuracy
    print(linear_svm_accuracy)
    print()

    print("Confusion matrix:")
    print()
    linear_svm_confusion_matrix = confusion_matrix(y_test, y_pred)
    experiment_results['confusion_matrix'] = linear_svm_confusion_matrix
    print(linear_svm_confusion_matrix)
    print()

    plot_confusion_matrix(linear_svm_confusion_matrix, classes=["Positive", "Negative"],
                          filename=os.getcwd() + '/experiment_' + str(
                              i) + '_confusion_matrix.png')

    linear_svm_precision_recall_fscore_support = precision_recall_fscore_support(y_test, y_pred)
    experiment_results['precision_recall_f1'] = linear_svm_precision_recall_fscore_support

    pos_precision = linear_svm_precision_recall_fscore_support[0][0]
    neg_precision = linear_svm_precision_recall_fscore_support[0][1]
    pos_recall = linear_svm_precision_recall_fscore_support[1][0]
    neg_recall = linear_svm_precision_recall_fscore_support[1][1]
    pos_f1 = linear_svm_precision_recall_fscore_support[2][0]
    neg_f1 = linear_svm_precision_recall_fscore_support[2][1]

    print("Positive precision:")
    print(pos_precision)
    print()

    print("Positive recall:")
    print(pos_recall)
    print()

    print("Positive F1:")
    print(pos_f1)
    print()

    print("Negative precision:")
    print(neg_precision)
    print()

    print("Negative recall:")
    print(neg_recall)
    print()

    print("Negative F1:")
    print(neg_f1)
    print()

    print("WEIGHTED F1:")
    linear_svm_f1 = f1_score(y_test, y_pred, average='weighted')
    experiment_results['weighted_F1'] = linear_svm_f1
    F1s.append(linear_svm_f1)
    print(linear_svm_f1)
    print()

    fpr, tpr, thresholds = roc_curve(y_test, y_prob[:, 0], pos_label=0)
    pos_auc = auc(fpr, tpr)
    experiment_results['fpr'] = fpr
    experiment_results['tpr'] = tpr
    experiment_results['pos_auc'] = pos_auc
    plot_roc(fpr, tpr, pos_auc, "Positive ROC",
             filename=os.getcwd() + '/experiment_' + str(i) + '_pos_roc.png')

    print("auc pos:")
    print(pos_auc)
    print()

    fnr, tnr, thresholds = roc_curve(y_test, y_prob[:, 1], pos_label=1)
    neg_auc = auc(fnr, tnr)
    experiment_results['fnr'] = fnr
    experiment_results['tnr'] = tnr
    experiment_results['neg_auc'] = neg_auc
    plot_roc(fnr, tnr, neg_auc, "Negative ROC",
             filename=os.getcwd() + '/experiment_' + str(i) + '_neg_roc.png')

    print("auc neg:")
    print(neg_auc)
    print()

    experiments_results[i] = experiment_results

final_ranking = np.sum(feature_ranking, axis=1)

print("Variables selected in ALL experiments:")
print(variable_names[final_ranking == num_experiments])
print()

save_object(experiments_results, os.getcwd() + '/linear_svm_results.pkl')
save_object(feature_ranking, os.getcwd() + '/feature_ranking.pkl')

features_info = np.array(list(zip(np.repeat('', len(variable_names)), np.repeat(0, len(variable_names)), np.repeat(0, len(variable_names)), np.repeat(0, len(variable_names)))), dtype=[('names', 'S12'), ('stability', '>i4'), ('performance (F1)', '>f4'), ('coefficients', '>f4')])
features_info['names'] = variable_names
features_info['stability'] = final_ranking
features_info['performance (F1)'] = np.repeat(np.mean(np.array(F1s)), len(variable_names))
features_info['coefficients'] = np.mean(coefficients, axis=1)

with open(os.getcwd() + '/features_info.csv', 'wb') as f:
    w = csv.writer(f)
    w.writerow(['names', 'stability', 'performance (F1)', 'linear SVM coefficients'])
    w.writerows(features_info)