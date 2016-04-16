import numpy as np
import datetime
import json
from random import randint
import sys
import binomial_distribution
import trend_estimator
import my_time
import math
import time

class ModifiedMonteCarlo():

#housekeeping functions for data management

    #to sample out occupancies from
    #expected input: training_data_set is a list of occupancies associated with the trianing_data_designation (season name)

    #full_training_dict: day_start: day: reservation:
    #FULL TRIANING DICT STRUCTURE: the days in the a day_start key must be consecutive.  IF there is a new season day inbetween, then it should be made into a new check-in key!
    #
    #created_at, end_status: ,checkin, checkout:,
    #tables: date_start: "r_of_i_t":numpy array
    #
    #
    #testing_start >= point_view_date

    def __init__(self, testing_start, testing_end, full_training_dict = None, point_of_view = 0):
        #big class variables
        self.training_length = len(full_training_dict.keys())
        self.testing_end = testing_end
        self.testing_start = testing_start
        #day trackers
        self.season_day_tracker = {0:[], 1:[], 2:[]}
        self.day_int_conversion = {}
        self.point_of_view = point_of_view
        #for each index t, the season designation
        self.t_season_tracker = np.zeros((1, self.training_length))
        self.point_of_view = point_of_view

        #season trend objects
        self.s_of_t = np.zeros( (1, self.training_length) )
        self.s_season_sums = np.zeros( (1, self.training_length) )

        #season: i: full np array[row : 1 is sum, row:2 is count]
        self.s_season_i_sums = {0: {}, 1: {}, 2: {} }
        self.s_week_average = np.zeros( (1, self.training_length) )
        #season trackers
        self.season_count = np.zeros((1, self.training_length))

        #reservation_tracker objects
        self.r_i_t = np.zeros( (365, self.training_length) )
        self.r_j_t = np.zeros( (1, self.training_length) )

        #day: cancellation threshold
        #self.c_season_i_sum = np.zeros((1, self.training_length))
        #self.c_threshold_t = np.zeros((1, self.training_length))
        self.cancellations = {0: {}, 1: {}, 2: {}}

        #season: length: nparray that tracks the sum on day t, wil be transformed later into: day: duration threhold: duration dict
        self.durations = {0:{}, 1:{}, 2:{}}
        #self.durations = {}

        if full_training_dict:
            self.fill_global_values(full_training_dict)

        #make trend
        self.start_t = self.day_int_conversion[testing_start]
        end_t = self.day_int_conversion[testing_end]

        self.trend = trend_estimator.TrendEstimator(point_of_view, self.season_day_tracker, self.t_season_tracker, datetime.date(2014, 1, 2), datetime.date(2016, 1, 30), self.s_of_t, self.s_season_sums, self.s_season_i_sums, self.s_week_average)

        #the stuff that needs to be calculated later
        self.binomial_distribution = binomial_distribution.BinomialDistribution()

        #make binomial stuff
        self.update_binomial_distribution()

    def fill_global_values(self, training_data_set):

        sorted_days = sorted([datetime.datetime.strptime(day, "%Y-%m-%d").date() for day in training_data_set.keys()])
        #update start and stop
        self.training_start = sorted_days[0]
        self.training_stop = sorted_days[len(sorted_days) - 1]

        #store values in a list and computer later
        trend_week_counter = []
        trend_season_i_tracker = {0:{}, 1: {}, 2: {}}
        trend_season_sum_tracker = {0: [], 1: [], 2: []}

        #cancellation and duration trackers

        for t, day in enumerate(sorted_days):
            #initialisation
            season = int(training_data_set[str(day)]['k_cluster'])

            #day: "season": , "t":
            self.day_int_conversion[day] = t
            self.season_day_tracker[season].append(t)
            self.t_season_tracker[0, t] = season

            #Life Hack: center s_of_t where 0 = 1 to make time_series prediction happy
            ##do trend stuff
            self.s_of_t[0, t] = 1
            cancellation_count = 0

            if training_data_set[str(day)]['reservations']:
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

                    #do duration, it should exist
                    duration = (checkout - day ).days
                    try:
                        self.durations[season][duration] += 1
                    except KeyError:
                        self.durations[season][duration] = 1

                    #increment r_of_j_t, total reservations made regardless
                    #self.r_i_t_over_r_j_t[i, t] += 1

                    #do reservations and cancellations
                    if reservation_data['status'] in ['CANCELLED']:
                        cancellation_count += 1

                    if reservation_data['status'] in ['CONFIRMED', 'BLOCKEDBYCONFIRMED', 'CANCELLATIONREQUESTED', 'DOUBLEBOOKING', 'UNAVAILABLE']:
                            #only increment for successful occupations, aka: "arrived reservation"
                            self.s_of_t[0, t] += 1

            #do cancellation
            try:
                self.cancellations[season][day.weekday()].append(cancellation_count)
            except KeyError:
                self.cancellations[season][day.weekday()] = [cancellation_count]


            #do trend stuff now
            #day of week sums
            try:
                trend_season_i_tracker[season][day.weekday()].append(self.s_of_t[0, t])
            except KeyError:
                trend_season_i_tracker[season][day.weekday()] = [self.s_of_t[0, t]]

            #update all the season i tables
            for this_season in trend_season_i_tracker.keys():
                for weekday in trend_season_i_tracker[this_season].keys():
                    try:
                        self.s_season_i_sums[this_season][weekday][0, t] = sum(trend_season_i_tracker[this_season][weekday])
                        self.s_season_i_sums[this_season][weekday][1, t] = len(trend_season_i_tracker[this_season][weekday])
                    except KeyError:
                        self.s_season_i_sums[this_season][weekday] = np.zeros( (2, self.training_length) )
                        self.s_season_i_sums[this_season][weekday][0, t] = sum(trend_season_i_tracker[this_season][weekday])
                        self.s_season_i_sums[this_season][weekday][1, t] = len(trend_season_i_tracker[this_season][weekday])

            #season_week_averages: calculate to see if a new week has started
            trend_week_counter.append(self.s_of_t[0,t])

            if t > 0 and (season != self.t_season_tracker[0, t-1] or t == len(sorted_days) - 1 or len(trend_week_counter) == 7):

                #a new week has started
                this_week_average = float(sum(trend_week_counter))/len(trend_week_counter) #should never = 0

                for x in xrange(0, len(trend_week_counter), 1):
                    #update final weekaverages
                    self.s_week_average[0, t - x] = this_week_average

                #clear
                trend_week_counter = []

            #do season sum
            #Never hits this check :)
            if self.s_of_t[0,t] == 0:
                print "test! monteCarlo_new, 188"

            trend_season_sum_tracker[season].append(self.s_of_t[0,t])
            self.s_season_sums[0, t] = sum(trend_season_sum_tracker[season])
            self.season_count[0, t] = len(trend_season_sum_tracker[season])

        #do full season cancellations and durations
        for season in self.durations.keys():
            #durations
            duration_sum = sum(self.durations[season].values())
            threshold = 100
            for duration, count in self.durations[season].iteritems():
                self.durations[season][threshold] = duration
                threshold -= int(100 * float(count)/duration_sum)

                del self.durations[season][duration]

        for season in self.cancellations.keys():
            for weekday, full_list in self.cancellations[season].iteritems():
                self.cancellations[season][weekday] = int(100 * float(sum(full_list))/len(full_list))


    def update_binomial_distribution(self):

        for day in my_time._daterange(self.testing_start, self.testing_end):
            point_of_view_date = day - datetime.timedelta(self.point_of_view)
            t = self.day_int_conversion[day]
            try:
                point_view_date_t = self.day_int_conversion[point_of_view_date]
            except KeyError: #poitn of view is too early, when this is hte case we will take t because this is before real training starts
                point_view_date_t = t
                point_of_view_date = day

            history_start = point_of_view_date - datetime.timedelta(365)
            if history_start < datetime.date(2014, 1, 1):
                history_start = datetime.date(2014, 1, 1)

            #find best match day
            match_day = self.find_best_match(day, history_start, point_of_view_date, self.t_season_tracker[0, t])
            match_t = (match_day - datetime.date(2014, 1, 1)).days

            #do binomial distribution stuff
            proposed_trend = self.trend.predict_forecasted_s_t(t) - 1

            if proposed_trend > 0:
                print "TEST proposed_trend, ", proposed_trend
            date_start = time.time()
            #make b_hat_i_t
            b_hat_i_t_column = self.make_b_hat_i_t(point_of_view_date, self.t_season_tracker[0, t], proposed_trend)

            bhat_bottleneck = time.time() - date_start
            pause = time.time()
            self.binomial_distribution.add_data(b_hat_i_t_column, t, self.r_i_t[:, match_t], self.t_season_tracker[0, t])

            add_data_bottleneck = time.time() - pause

            #print "binomial: ", day, ": make_b_hat_i_t, ", bhat_bottleneck, ", binomial_dstribution.add_data: ", add_data_bottleneck

    def find_best_match(self, day, history_start, point_view_date, season):
        search_weekday = day.weekday()

        #must have at least one nth weekday
        nth_weekday = ((day - point_view_date).days / 7) + 1

        i_counter = []
        for test_t in self.season_day_tracker[season]:
            test_day = datetime.date(2014, 1, 1) + datetime.timedelta(test_t)
            if test_day.weekday() == search_weekday:
                i_counter.append(test_day)
            if len(i_counter) == nth_weekday:
                return test_day

        #if we never find an appropriate day, then we are going to return the last day that matches.  This should not happen with the limited test range

        return i_counter[-1]

    #point of view specifies the limit of knowledge known for the t used to be predicted
    def make_b_hat_i_t(self, point_of_view_date, season, proposed_trend):
        final = []
        #season_length needs to be history
        point_view_t = self.day_int_conversion[point_of_view_date]
        start_t = point_view_t - 365
        if start_t < 0:
            start_t = 0

        for i in xrange(0, 365):
            inner_sum = 0

            all_valid_t = [entry for entry in self.season_day_tracker[season] if entry < point_view_t and entry >= start_t]

            for t in sorted(all_valid_t):
                if self.r_j_t[0, t] == 0:
                    continue
                if self.r_i_t[0,t] > 1:
                    print "there are multiple reservations being made"

                inner_sum += float(self.r_i_t[i, t])/self.r_j_t[0, t]

            b_hat_i_t = (float(inner_sum)/ len(all_valid_t)) * proposed_trend

            if math.isnan(b_hat_i_t):
                print "we have nan again"
                sys.exit()

            final.append(b_hat_i_t)

        return np.array(final)

    #PREDICTION AREA OF CODE

    '''
    i is the day ahead that we are looking at, to predict for day t
    returns an int number of predicted reservations, minus cancellations
    day can be a datetime object

    returns an int for the number of predicted reservations for the day, on the ith day before checkin
    '''
    def _predict_reservations(self, day, i):
        this_t = self.day_int_conversion[day]
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
    def _predict_cancellations(self, day, predicted_reservations, i_in_week):

        if not predicted_reservations.keys():
            return None

        final = {}
        t = self.day_int_conversion[day]
        season = self.t_season_tracker[t]

        cancellation_threshold = self.c_threshold_t[season][day.weekday()]

        for i, duration_list in predicted_reservations.iteritems():
            if not durations_list:
                continue

            for item in duration_list:
                choice = randint(1, 101)
                if choice >= cancellation_threshold: #then we keep this
                    try:
                        final[i].append(item)
                    except KeyError:
                        final[i] = [item]
        return final


    #t is the day array int in the season
    '''
    expecting prediction_dict to have the keys as threshold values, and the values the actual "predicted value"
    '''
    def _predict_duration(self, day):
        season = self.t_season_tracker[self.day_int_conversion[day]]
        choice = randint(1, 101)

        try:
            sorted_thresholds = sorted(self.durations[season].keys())
        except Exception: #not existing
            #there were no durations for this day, which should be possible if predicitng past a point where there has been reservations in the history
            print "check this listing and prediction day because we havne't had any reservation data yet"
            sys.exit()

        for x, threshold in enumerate(sorted_thresholds):
            try:
                if sorted_thresholds[x+1] >= choice:
                    return self.durations[season][threshold]
            except KeyError: #finished the list already
                return self.durations[season][threshold]


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


def test():

    with open('../data/sample.json') as jsonFile:
        reservation_dict = json.load(jsonFile)

    #(self, full_training_dict = None, k_iterations = 1)

    #testing_start, testing_end, full_training_dict = None, point_of_view = 0)
    start = time.time()
    monte_defined = ModifiedMonteCarlo(datetime.date(2015, 1, 29), datetime.date(2016, 1, 29), reservation_dict, 0)
    monte_stop = time.time() - start

    #good prediction should predict 0 for all
    print "hello, this is a break for MonteCarlo 498"

if __name__ == '__main__':

    test()

