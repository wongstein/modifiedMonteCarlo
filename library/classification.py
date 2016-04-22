#import database

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


def test():
    sample = {'empty_fOne': 0.9689265536723164, 'empty_precision': 0.9397260273972603, 'occupancy_precision': None, 'false_false': 22, 'correct_overall': 0.9397260273972603, 'occupancy_fOne': None, 'empty_recall': 1.0, 'true_false': 343, 'false_true': 0, 'true_true': 0, 'occupancy_recall': 0.0}

    save_to_database("monte_carlo_average_results", "save_to_database_test", "test", sample)

if __name__ == '__main__':
    test()



