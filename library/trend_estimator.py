from holtwinters import estimator, holtwinters
import datetime
import my_time
import numpy as np
import sys
import math
'''
this is a helper class to make the the trend estimator for the Modified MonteCarlo
'''

class TrendEstimator():
    #input: (in day order:) check_in: day: s(t), day: s(t), check-IN...
    def __init__(self, season_stuff_dict, s_of_t):
        #initialise important tables
        self.week_averages = season_stuff_dict['week_average']
        self.t_weekday_converter = s_of_t[1, : ]
        self.t_season_converter = s_of_t[2, : ]

        self.day_week_median = {}
        self.season_averages = {0: None, 1: None, 2: None}

        #data processing:
        self._make_deseasonalised_tables(season_stuff_dict)

        #order of deseasonalisation:
        #divide s of t by it's season average
        s_des1_1 = self.deseasonalise_season_average(s_of_t[0,:].tolist())

        #take out week averages
        #input: key, week_counter= [s_des1, s_des2]
        s_prime_t = self.deseasonalise_week_average(s_des1_1)

        #take out day of week medians
        s_des_t = self.de_seasonalise_day_week(s_prime_t)

        #make holtwinters, hacked it to have just 2 equal seasons, which after deseasonalisation doesn't exit.  But okay
        self.holtwinters_object = holtwinters.HoltWintersEstimator(s_des_t, 3, len(s_des_t)/3)


    def _make_deseasonalised_tables(self, season_trend_stuff):
        #make season averages and also season week data
        #key will hold the index of the first int in the season's range
        #
        #
        #
        '''
        season_trend_stuff = {
        0:{'day_week_averages':  {0: [], 1:[], 2: [], 3: [], 4: [], 5: [], 6: []}, 'season_averages' = []},
        1: {'day_week_averages':  {0: [], 1:[], 2: [], 3: [], 4: [], 5: [], 6: []}, 'season_averages' = []},
        2: {'day_week_averages':  {0: [], 1:[], 2: [], 3: [], 4: [], 5: [], 6: []}, 'season_averages' = []},

        'week_averages': np.zeros(1, Monte_Carlo_Base.s_of_t_value.shape[1])}
        '''

        for season in [0, 1, 2]:
            #season_averages
            season_average = float(sum(season_trend_stuff[season]['average'])) / len(season_trend_stuff[season]['average'])

            self.season_averages[season] = season_average

            #day of week_averages
            self.day_week_median[season] = {}


            for day in [0, 1, 2, 3, 4, 5, 6]:
                if not season_trend_stuff[season]['day_week'][day]:
                    self.day_week_median[season][day] = 0
                    continue

                median = np.median(np.array(season_trend_stuff[season]['day_week'][day]))

                self.day_week_median[season][day] = median



    '''
    this_input is a list
    '''
    def de_seasonalise_day_week(self, this_input):
        final = []

        #dict: season: value

        for t in xrange(0, len(this_input), 1):
            t_season = int(self.t_season_converter[t])
            t_day = int(self.t_weekday_converter[t])

            if this_input[t] == 0:
                final.append(0)
                continue

            try:
                final.append(float(this_input[t])/self.day_week_median[t_season][t_day])
            except ZeroDivisionError: #then this was
                print "We shouldn't have a zeroDivisionError for day of week averages"
                sys.exit()
        return final

    def deseasonalise_season_average(self, this_input):
        final = []
        for t in xrange(0, len(this_input), 1):
            t_season = int(self.t_season_converter[t])

            if this_input[t] == 0:
                final.append(0)
                continue

            try:
                final.append(float(this_input[t])/self.season_averages[t_season])
            except ZeroDivisionError: #then this was
                print "We shouldn't have a zeroDivisionError for day of week averages"
                sys.exit()
        return final

    def deseasonalise_week_average(self, this_input):
        this_thing = self.week_averages

        final = []

        for x in xrange(0, len(this_input), 1):
            #should never be 0
            to_add = float(this_input[x])/self.week_averages[0, x]

            final.append(to_add)

        return final

    '''
    day and point of view are ints.  Day is the int after the last full day of trining that we are predicting for.  Point of view is the  perspective we hav after training
    keep in mind that now, day represents a "best matched day", which exists in the history

    Because of "best_matched_day" strategy, the holtwinter's base time is always the end of it's training (or season size)

    automatically puts in the t_needed
    '''
    def predict_forecasted_s_t(self, day_t):


        predicted_s_of_t = self.holtwinters_object.estimate(day_t + 1, day_t)

        season = int(self.t_season_converter[day_t])
        day_week = int(self.t_weekday_converter[day_t])

        #think about how to do the day_of_week_averages, which will be messed up
        #
        reseasonalised = predicted_s_of_t * self.season_averages[season] * self.day_week_median[season][day_week] * self.week_averages[0, day_t]

        return reseasonalised


def test_all_10():
    #input: (in day order:) check_in: day: s(t), day: s(t), check-IN..
    test_input = {"today": {datetime.date(2014, 1, 1): 10, datetime.date(2014, 1, 2): 10, datetime.date(2014, 1,3): 10, datetime.date(2014, 1, 4): 10, datetime.date(2014, 1, 5): 10, datetime.date(2014, 1, 6): 10, datetime.date(2014, 1, 7): 10 } }
    #expectation should be that everything is 10

    my_estimator = TrendEstimator(test_input)

    prediction = my_estimator.predict_forecasted_s_t(2, 2)

    #expect prediction to be 10

    print "hello"

def test():
    import MonteCarlo
    import json
    import Historical_Monte
    import time
    with open('../data/sample.json') as jsonFile:
        reservation_dict = json.load(jsonFile)

    #(self, full_training_dict = None, k_iterations = 1)
    monte_base_start_time = time.time()
    listing_Monte = MonteCarlo.ModifiedMonteCarlo_Base(reservation_dict)
    monte_time_cost = time.time() - monte_base_start_time


    end_date = datetime.date(2016, 1, 20)

    monte_defined_base = time.time()
    monte_defined = Historical_Monte.Historical_Monte(listing_Monte,end_date )
    monte_cost = time.time() - monte_defined_base

    prediction = my_estimator.predict_forecasted_s_t(1, 1)

    #expect 1
    print prediction

if __name__ == '__main__':
    #test_all_10()
    test()



