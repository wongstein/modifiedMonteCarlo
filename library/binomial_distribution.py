import numpy as np
from random import randint

'''
gets truncated full trianing period
input all the b_hat_i_t predictions, np: 365, length_season
and all the r_i_t full history, np: (365, length_season)
'''
class BinomialDistribution():
    def __init__(self):
        #key is t, value is the variance value for that t
        self.inner_sum_by_season = {0: [], 1: [], 2: []}

        #Where t is the key, and t correlates with the testing_t
        #t: i: [possible_np combos_dict]
        self.all_n_p = {}

    '''
    adding options day by day, column by column
    output is adding to the inner sum calculations in the variance
    also creating all NP options
    season length kept tracked of

    this goes day by day, so no reason why we can't do the variance also
    '''
    def add_data(self, b_hat_i_t_column, t, r_i_t_best_match, season):

        possible_n_p = {}
        inner_sum = 0

        #don't do calculations for days we will never predict for
        if t < 365:
            return

        if max(b_hat_i_t_column) == 0:
            possible_n_p = {i: [{'n': 0, 'p': 1}] for i in range(0, 365)}
            return

        for i in xrange(0, 365, 1):
            #do NP options
            #will be i: [choices_dict]
            #
            possible_n_p[i] = self.calculate_all_n_p(b_hat_i_t_column[i])

            '''
            if len(possible_n_p[i]) == 1:
                print "TEST 37"
            '''
            #calculate inner sum
            inner = b_hat_i_t_column[i] + r_i_t_best_match[i]
            inner_sum += (inner * inner)

        self.inner_sum_by_season[season].append(inner_sum)

        #do variance calculations
        t_variance = float(sum(self.inner_sum_by_season[season]))/len(self.inner_sum_by_season[season])

        #weed out the weak NP
        self.all_n_p[t] = self.weed_n_p(possible_n_p, t_variance)

    def calculate_all_n_p(self, b_hat_i_t):

        #if no reservation hope, then no point in doing this
        if b_hat_i_t == 0:
            return [{'n': 0, 'p': 1}]

        final = []

        #so generally we are dealing with very small probabilities,
        #So let's find probablities just for a small
        for n in range(1, 4):
            this_probability = float(x)/100
            n = float(b_hat_i_t)/this_probability

            if n < 1: #we don't have an integer
                if {'n': 0, 'p': 1} not in final:
                    final.append({'n': 0, 'p': 1})
                continue

            choice = {'n': n, 'p': this_probability}

            final.append(choice)

        return final

    def find_range(self, b_hat_i_t):
        #not necessarily within 1 percent to have a reservation (if there is only one reservation on a day in a season, it can be at best 1/300)
        pass

    def weed_n_p(self, possibilities_dict, t_variance):
        final = {}
        for i, possibilities_list in possibilities_dict.iteritems():

            #keep possibility_dict if it's a situation where b_hat_i is 0
            if len(possibilities_list) == 1 and possibilities_list[0]['n'] == 0:
                final[i] = possibilities_list
                continue

            for possibility_dict in possibilities_list:
                binomial_variance = float(possibility_dict['n']) * possibility_dict['p'] * (1 - possibility_dict['p'])

                if binomial_variance == t_variance:
                    try:
                        final[i].append(possibility_dict)
                    except KeyError:
                        final[i] = [possibility_dict]

        return final

    # i refers to the day ahead of the full history t predicting for
    def get_n_p(self, i, t):
        tot_options = len(self.all_n_p[i][t])

        if tot_options == 1:
            return self.all_n_p[i][t][0]

        random_choice = randint(0, tot_options)

        #output: dictionary that has "n": and "p": choice
        return self.all_n_p[i][t][random_choice]


def test():
    import time
    import datetime
    import MonteCarlo_new
    import json
    import trend_estimator


    #test for 10 days
    start_date = datetime.date(2015, 1, 20)
    end_date = datetime.date(2016,1, 30)


    with open('../data/sample.json') as jsonFile:
        reservation_dict = json.load(jsonFile)

    #(self, full_training_dict = None, k_iterations = 1)

    #testing_start, testing_end, full_training_dict = None, point_of_view = 0)
    start = time.time()
    monte_defined = MonteCarlo_new.ModifiedMonteCarlo(datetime.date(2015, 1, 29), datetime.date(2016, 1, 29), reservation_dict, 0)
    monte_stop = time.time() - start

    #good prediction should predict 0 for all
    print "hello, this is a break for MonteCarlo 468"

if __name__ == '__main__':
    test()

