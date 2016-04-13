from sklearn.svm import LinearSVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.ensemble import RandomForestClassifier
from scipy.sparse import coo_matrix
from sklearn import tree
from sklearn import svm
import numpy as np
import database

class classification():
    model = None
    model_name = ""

    def __init__(self, choice):
        self.model_name = choice

    def train_with(self, training_data_list, answers):
        #put data in right format
        training_data = self.get_sparse_matrix(training_data_list)

        if training_data is not False:

        #make model
            if self.model_name == "random_forest":
                forest = RandomForestClassifier(n_estimators=100)
                self.model = forest.fit(training_data.todense(), answers)
            elif self.model_name == "centroid_prediction":
                clf = NearestCentroid()
                self.model = clf.fit(training_data, answers)
            elif self.model_name == "linearSVC":
                SVC = LinearSVC()
                self.model = SVC.fit(training_data.todense(), answers)
            elif self.model_name == "nearest_neighbor":
                near = KNeighborsClassifier()
                self.model = near.fit(training_data.todense(), answers)
            elif self.model_name == "decision_tree":
                clf = tree.DecisionTreeClassifier()
                self.model = clf.fit(training_data.todense(), answers)
            elif self.model_name == "svc":
                clf = svm.SVC()
                self.model = clf.fit(training_data, answers)

    def predict(self, testing_data):
        testing_data_matrix = self.get_sparse_matrix(testing_data)

        if testing_data_matrix is not False and self.model:

            if self.model_name in ["random_forest", "linearSVC", "nearest_neighbor", "decision_tree"]:
                return self.model.predict(testing_data_matrix.todense())
            else:
                return self.model.predict(testing_data_matrix)

        else:
            #for debugging
            return False

    def instructions(self):
        print "My model_name is ", self.model_name
        print "to change the model, use: classify_with(self, model_name)"
        print "model names are: random_forest, centroid_prediction, linearSVC, nearest_neighbor, decision_tree, svc"
        print "evaluation "

    '''
    hopefully gives the sparse matrix
    input is list of list
    '''
    def get_sparse_matrix(self, mydata):
        row = []
        col = []
        data = []

        for x, entry in enumerate(mydata):
            #structure of doc is a list of lists.
            for i, item in enumerate(entry):
                #item structure: [word index (row value), word_count]
                row.append(x)
                col.append(i)
                data.append(item)

        #convert to np array
        row = np.asarray(row)
        col = np.asarray(col)
        data = np.asarray(data)
        try:
            return coo_matrix((data, (row, col)))
        except Exception as e:
            print e
            print "row, " , row
            print "col, " , col
            print "len of data ", len(data)
            return False


'''
TESTING
expecting binary inputs from prediction and classification
0 is false
1 is true
'''

'''
the following methods takes a dictionary result of test_prediction to calculate measuring
values
'''
class results():
    def __init__(self, prediction, classification):
        self.true_true = 0
        self.true_false = 0
        self.false_true = 0
        self.false_false = 0

        self.prediction = prediction
        self.classification = classification

        self.make_results()
        self.make_precision()
        self.make_recall()
        self.make_fOne()
        self.make_correctovertotal()


    def make_results(self):

        if len(self.prediction) != len(self.classification):
            print "prediction and classification inputs are not the same size"
            self.results = None
        for i in range (0, len(self.prediction)):
            if self.prediction[i] == self.classification[i]:
                if self.prediction[i] == 1:
                    self.true_true += 1
                else:
                    self.true_false += 1
            else:
                if self.prediction[i] == 1:
                    self.false_true += 1
                else:
                    self.false_false += 1

    #how many of the selected items are relevant (how good was it at guessing occupancy)
    #true_truths/ (total number of truths guessed = "true truths)
    #Of those that I guess to be X, how many were actually X

    def make_precision(self):
        try:
            self.occupancy_precision = float(self.true_true)/(self.true_true + self.false_true)
        except Exception as e:
            #most likely float by zero error
            self.occupancy_precision = None
        try:
            self.empty_precision = float(self.true_false)/(self.true_false + self.false_false)
        except Exception as e:
            self.empty_precision = None


    def make_recall(self):
    #how many relevant items were selected
    #true_truths/ total_truths
    #Of all the X's in the sample, how many did I find?
        try:
            self.occupancy_recall = float(self.true_true)/(self.true_true + self.false_false)
        except Exception as e:
            self.occupancy_recall = None
        try:
            self.empty_recall = float(self.true_false)/(self.true_false + self.false_true)
        except Exception as e:
            self.empty_recall = None

    def make_fOne(self):
        try:
            self.occupancy_fOne = 2 * float(self.occupancy_precision * self.occupancy_recall)/(self.occupancy_precision + self.occupancy_recall)
        except Exception as e:
            self.occupancy_fOne = None
        try:
            self.empty_fOne = 2 * float(self.empty_precision * self.empty_recall)/(self.empty_precision + self.empty_recall)
        except Exception as e:
            self.empty_fOne = None

    def make_correctovertotal(self):
        correct = self.true_true + self.true_false
        total = correct + self.false_true + self.false_false

        try:
            self.overall = float(correct)/total
        except Exception as e:
            print "no data was given to test with, it looks like..."
            self.overall = None

    def get_results(self):

        return {"true_true": self.true_true, "true_false": self.true_false, "false_false": self.false_false, "false_true": self.false_true, "occupancy_precision": self.occupancy_precision, "empty_precision": self.empty_precision, "correct_overall": self.overall, "occupancy_recall": self.occupancy_recall, "empty_recall": self.empty_recall, "occupancy_fOne": self.occupancy_fOne, "empty_fOne": self.empty_fOne}


#rewritten for monte_carlo prediction requirements
def save_to_database(table_name, experiment_name, city_name, full_dict, method =True):
    thesis_data = database.database("Thesis")

    #delete similar entries
    query = "DELETE FROM `" + table_name + "` WHERE `city` = '" + city_name + "' AND `experiment` = '" + experiment_name + "';"
    #print query
    thesis_data.execute(query)

    print "saving to database " + table_name + " experiment results: " + experiment_name

    #put entries in, then the keys are lists and what I want to store are the true_true,
    if full_dict and isinstance(full_dict.keys()[0], long): #for individual storage
        insert_query = "INSERT INTO " + table_name + "  VALUES('%s','%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for listing_id, results in full_dict.iteritems():
            #experiment ,  city , listing_id, method, true_true, true_false, false_true, false_false, occupancy_precision, occupancy_recall, empty_precision, empty_recall, occupancy_fOne, empty_fOne, correct_overall
            to_insert = [experiment_name, city_name, listing_id]

            for this_thing in ["true_true", "true_false", "false_true", "false_false", "occupancy_precision", "occupancy_recall", "empty_precision", "empty_recall", "occupancy_fOne", "empty_fOne", "correct_overall"]:
                if results[this_thing]:
                    to_insert.append(method_results[this_thing])
                else:
                    to_insert.append("null")
            #print (insert_query % to_insert)
            thesis_data.execute(insert_query % tuple(to_insert))
    elif full_dict:
        insert_query = "INSERT INTO " + table_name + " VALUES('%s','%s',%s,%s,%s,%s,%s, %s)"
        #experiment ,  city, occupancy_precision, occupancy_recall, empty_precision, empty_recall, occupancy_fOne, empty_fOne,
        to_insert = [experiment_name, city_name]
        for this_thing in ["occupancy_precision", "occupancy_recall", "empty_precision", "empty_recall", "occupancy_fOne", "empty_fOne"]:
            if full_dict[this_thing]:
                to_insert.append(method_results[this_thing])
            else:
                to_insert.append("null")

        thesis_data.execute(insert_query % tuple(to_insert))

    thesis_data.destroy_connection()





