import numpy as np
from random import randint

'''
gets truncated full history trainining period
input all the b_hat_i_t predictions, np: 365, length_season
and all the r_i_t full history, np: (365, length_season)
'''
class BinomialDistribution():
    def __init__(self, b_hat_i_t_full, r_i_t_full):
        self.b_hat_i_t = b_hat_i_t_full
        self.r_i_t = r_i_t_full
        self.season_length = b_hat_i_t_full.shape[1]
        self.variance = None

        #calculations
        self.all_n_p = self.calculate_all_n_p()

        #calculate variance
        self.calculate_variance()

        #filter n and ps to be the right ones.  Final output is all_n_p
        #TEST!
        copy_all_n_p = self.all_n_p
        #self.calculate_variance_n_p(self.all_n_p)
        self.calculate_variance_n_p(copy_all_n_p)

    def calculate_variance(self):
        outer_sum = float(1)/(self.season_length * 365)

        inner_sum = 0
        for t in range(0, self.season_length):
            for i in range(0, 365):
                inside_square = self.b_hat_i_t[i, t] - self.r_i_t[i, t]
                square = inside_square * inside_square
                inner_sum += square

        self.variance = outer_sum * inner_sum


    def calculate_all_n_p(self):
        #t: i
        all_i_t = {}

        for t in range(0, self.season_length):
            all_i_t[t] = {}
            for i in range(0, 365):
                all_i_t[t][i] = []
                #for all possible probabilities
                #If the predicted
                if self.b_hat_i_t[0, t] == 0:
                    choice = {'n': 0, 'p': 0}
                else:
                    for x in range(1, 101):
                        this_probability = float(x)/100
                        choice = {'n': float(self.b_hat_i_t[0, t])/this_probability, 'p': this_probability}

                        all_i_t[t][i].append(choice)
        return all_i_t

    def calculate_variance_n_p(self, all_n_p):

        for t, all_is in all_n_p.iteritems():
            for i, possibilities_list in all_is.iteritems():
                for possibility_dict in possibilities_list:

                    empirical_variance = self.variance
                    binomial_variance = float(possibility_dict['n']) * possibility_dict['p'] * (1 - possibility_dict['p'])

                    if binomial_variance != empirical_variance and possibility_dict['n'] != 0: #keep possibility_dict if it's a situation where b_hat_i is 0
                        del possibility_dict

    #

    def get_n_p(self, i, t):
        tot_options = len(self.all_n_p[i][t])

        if not tot_options: #if it is 0
            return {'n': 0, 'p': 0}

        random_choice = randint(0, tot_options)

        #output: dictionary that has "n": and "p": choice
        return self.all_n_p[i][t][random_choice]

def test():
    b_hat_i = np.array([ [10, 10, 10], [10, 10, 10], [10, 10, 10] ])



