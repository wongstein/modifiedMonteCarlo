import numpy as np
import datetime
import json
import Historical_Monte
from random import randint
import sys

#implementation of the modified monteCarlo scheme

class ModifiedMonteCarlo_Base():

#housekeeping functions for data management

    #to sample out occupancies from
    #expected input: training_data_set is a list of occupancies associated with the trianing_data_designation (season name)

    #full_training_dict: day_start: day: reservation:
    #FULL TRIANING DICT STRUCTURE: the days in the a day_start key must be consecutive.  IF there is a new season day inbetween, then it should be made into a new check-in key!
    #
    #created_at, end_status: ,checkin, checkout:,
    #tables: date_start: "r_of_i_t":numpy array

    def __init__(self, testing_start, testing_end, full_training_dict = None, point_of_view = 0):
        #big class variables
        training_length = len(full_training_dict.keys())

        #season trend objects
        self.s_of_t = np.zeros( (1, training_length) )
        self.s_season_sums = np.zeros( (1, training_length) )
        self.s_season_i_sums = np.zeros( (1, training_length) )
        self.s_week_average = np.zeros( (1, training_length) )

        self.r_i_t = np.zeros( (365, training_length) )
        self.r_j_t = np.zeros( (1, training_length) )
        #self.r_i_t_over_r_j_t = np.zeros( (365, training_length) )
        self.c_of_t = np.zeros( (1, training_length) )

        self.durations_of_t = np.zeros((training_length, 15))

        self.day_int_conversion = {}
        self.season_day_tracker = {0:[], 1:[], 2:[]}

        self.fill_global_tables(full_training_dict)

        #fill inner values
        self.fill_seasonal_values(testing_start, testing_end, point_of_view)

        #make trend
        self.trend = trend_estimator.TrendEstimator(trend, self.s_of_t, )


        #sadly has to be like this: day: {cancellation/duration chance dict}
        self.cancellations = {}
        self.durations = {}


        #make binomial distribution
        self.binomial_distribution = binomial_distribution.BinomialDistribution(b_hat_i_t, Monte_Carlo_Base.r_i_t[:, self.start_t: self.end_t])

    '''
    THIS IS WRITTEN FOR when the clusters days are ordered by cluster and ARE NOT necessarily consecutive, however it is
    IF this is the table used, it's important that when in prediction, you calculate the day_int of the day in the cluster's individual calendar, or make a calendar dict to keep track.
    trianing_data comes in like: day: {'reservations': {}, 'k_cluster': ,'occupancy': }
    '''

    def fill_global_tables(self, training_data_set):
        #full reservation counts for t
        #week_number: i:count
        #duration_length: count

        #only 3
        sorted_days = sorted([datetime.datetime.strptime(day, "%Y-%m-%d").date() for day in training_data_set.keys()])

        season_
        for t, day in enumerate(sorted_days):
            season = int(training_data_set[str(day)]['k_cluster'])
            #day: "season": , "t":
            self.day_int_conversion[day] = t
            self.season_day_tracker[season].append(day)

            #Life Hack: center s_of_t where 0 = 1 to make time_series prediction happy
            self.s_of_t[0, t] = 1

            if not training_data_set[str(day)]['reservations']:
                continue

            i_collection = []
            self.r_j_t[0, t] = len(training_data_set[str(day)].keys())
            for x, reservation_id in enumerate(training_data_set[str(day)]['reservations'].keys()):
                reservation_data = training_data_set[str(day)]['reservations'][reservation_id]

                #convert dates to the right format

                enquiry_day = datetime.datetime.strptime(reservation_data['created_at'], "%Y-%m-%d %H:%M:%S").date()
                checkout = datetime.datetime.strptime(reservation_data['checkout'], "%Y-%m-%d %H:%M:%S").date()

                i = (day - enquiry_day).days

                #increment r_i_t
                self.r_i_t[i, t] += 1
                if i < 0:
                    print "input wrong for enquiry day in fill_tables_by_cluster"
                    #sys.exit()
                i_collection.append(i)

                #do duration
                duration = (checkout - day ).days
                if duration:
                    self.durations_of_t[t, x] = duration

                #increment r_of_j_t, total reservations made regardless
                #self.r_i_t_over_r_j_t[i, t] += 1

                #do reservations and cancellations
                if reservation_data['status'] in ['CANCELLED']:
                    #increments regardless
                    self.c_of_t[0, t] += 1

                if reservation_data['status'] in ['CONFIRMED', 'BLOCKEDBYCONFIRMED', 'CANCELLATIONREQUESTED', 'DOUBLEBOOKING', 'UNAVAILABLE']:
                        #only increment for successful occupations, aka: "arrived reservation"
                        self.s_of_t[0, t] += 1

            '''
            #finish doing r-it over r-jt
            for i in i_collection:
                self.r_i_t_over_r_j_t[i, t] = float(self.r_i_t[i, t])/r_j_t
            '''

    def fill_seasonal_values(self, testing_start, testing_end, point_of_view):
        #make b_hat_i
        b_hat_i = None
        #make b_hat_i_t


        for day in my_time._daterange(testing_start, testing_end):

    def make_b_hat_i_t(self, b_hat_i, duration):
        final = np.zeros( (365, duration) )
        for t in xrange(0, duration, 1):
            #update season to year conversion
            proposed_trend = self.trend.predict_forecasted_s_t(t) - 1
            for i in xrange(0, 365, 1):

                #for the situation where s_of_t has been normalised around 1, thus the minus 1 later
                if proposed_trend < 0:
                        proposed_trend = 0

                b_hat_i_t = b_hat_i[0, i] * proposed_trend

                #TEST
                if math.isnan(b_hat_i_t):
                    print "we have nan again"
                    sys.exit()

                final[i, t] = b_hat_i_t
        return final

    #PREDICTION AREA OF CODE

    '''
    i is the day ahead that we are looking at, to predict for day t
    returns an int number of predicted reservations, minus cancellations
    day can be a datetime object

    returns an int for the number of predicted reservations for the day, on the ith day before checkin
    '''
    def _predict_reservations(self, day, i):
        this_t = int( (self.day - self.start_date).days )
        season = self.t_seasons[0, this_t]
        predicted_reservations = 0

        #figure out year_t
        #year_t = self.season_tables[season]['season_t_to_year_t_conversion'][0, season_t]

        #randomly gives a n and p from this day's n,p table
        n_p_dict = self.binomial_distribution.get_n_p(i, this_t)

        #in case when there was no reservation data or no chance of the reservation materialising
        if n_p_dict['n'] == 0 or n_p_dict['p'] == 0:
            return 0

        #probability is the probabiliyt that the reservation will materialise for day t, i days in advance
        threshold = int(n_p_dict['p'] * 100)

        for x in xrange(0, n_p_dict['n'], 1):
            random_pick = randint(1, 100) #includes the ends
            if random_pick < threshold:
                predicted_reservations += 1

        return predicted_reservations

    '''
    predicted_reservations: are for a day, and it's a dict where i is the key, with a list of durations.  Known durations are full ints, predicted reservations are 0

    Only predicted reservations are passed into this
    '''
    def _predict_cancellations(self, season, predicted_reservations, i_in_week):

        final = []

        tot_cancellations_threshold = self.self.season_tables[season]['c_of_i_week'][i_in_week]

        for i, duration_list in predicted_reservations.iteritems():
            for item in duration_list:
                choice = randint(1, 101)
                if choice > tot_cancellations_threshold: #then we keep this
                    try:
                        final[i].append(item)
                    except KeyError:
                        final[i] = [item]
        return final


    #t is the day array int in the season
    '''
    expecting prediction_dict to have the keys as threshold values, and the values the actual "predicted value"
    '''
    def _predict_duration(self, season):

        choice = randint(1, 101)

        sorted_thresholds = sorted(prediction_dict.keys())

        for x, threshold in sorted_thresholds:
            try:
                if sorted_thresholds[x+1] >= choice:
                    return self.season_tables[season]['durations'][threshold]
            except KeyError: #finished the list already
                return self.season_tables[season]['durations'][threshold]


    '''
    This is the main prediction function
    day can be a datetime object
    original_reservations_dict: day: [i: duration]

    default to predicting at least up to the day before prediction

    matched_day is a datetime date object, and it should exist in the training history as a t_int

    day_known_reservation_dict: i: [durations]]
    '''
    def predict(self, matched_day, day_known_reservations_dict, point_of_view = 0):
        #must be datetime object

        #the key is i before checkin day
        if day_known_reservations_dict.keys():
            tot_reservations_predicted = day_known_reservations_dict
        else:
            tot_reservations_predicted = {}

        for i in xrange(0, point_of_view, 1):
            proposed_reservations = self._predict_reservations(matched_day, i)
            if proposed_reservations < 0:
                print "we have a negative number of reservations proposed."
                sys.exit()

            if proposed_reservations > 0:
                for x in xrange(0, proposed_reservations, 1):
                    try:
                        #zero signifies no known duration
                        tot_reservations_predicted[i].append(0)
                    except KeyError:
                        tot_reservations_predicted[i] = [0]

        if not tot_reservations_predicted:
            return 0

        #make cancelations
        season = self.t_seasons[0, int( (matched_day - self.start_date).days )]

        tot_reservations_predicted = self._predict_cancellations(season, tot_reservations_predicted, matched_day.weekday())

        #make durations
        for i, duration_list in tot_reservations_predicted:
            for item in durations_list:
                if duration == 0:
                    duration = self._predict_duration(season)
        #returns r
        return tot_reservations_predicted

def test(): #outdated
    #make sample
    import Historical_Monte

    #test for 10 days
    start_date = datetime.date(2015, 1, 20)
    end_date = datetime.date(2016,1, 30)


    with open('../data/sample.json') as jsonFile:
        reservation_dict = json.load(jsonFile)

    #(self, full_training_dict = None, k_iterations = 1)
    listing_Monte = ModifiedMonteCarlo_Base(reservation_dict)

    end_date = datetime.date(2015, 1, 20)

    monte_defined = Historical_Monte.Historical_Monte(listing_Monte,end_date )


    #good prediction should predict 0 for all
    print "hello"

if __name__ == '__main__':

    test()
    print "hello"
