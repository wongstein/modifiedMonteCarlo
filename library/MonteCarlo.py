import trend_estimator
import binomial_distribution
import numpy as np
import datetime
import json
import math
from random import randint
import sys
#implementation of the modified monteCarlo scheme

class ModifiedMonteCarlo():

#housekeeping functions for data management
    def add_training(self, training_data_set):
        #add data to training data
        for key, keys_data in training_data_set.iteritems():
            self.training_data_set[key] = keys_data
            if key in self.tables.keys():
                print "Hey you are adding training data with a key that already exists in the MonteCarlo table dict, " , key
                return

            self.tables[key] = self.make_tables(len(keys_data.keys() ) )
            self.s_of_t[key] = {}

    def delete_training(self, training_keys = None):
        if training_keys:
            for key in training_keys:
                del self.training_data_set[key]
                del self.tables[key]
                del self.s_of_t[key]

        #repopulate the data to represent the partially filled data
        for key in training_data_set.keys():
            self.fill_tables(key, len(training_data_set[keys].keys()) )

        else: #delete it all!
            self.training_data_set = {}
            self.tables = {}
            self.s_of_t = {}
            self.b_hat_of_i = np.zeros( (365, 365) )

    #to sample out occupancies from
    #expected input: training_data_set is a list of occupancies associated with the trianing_data_designation (season name)

    #full_training_dict: day_start: day: reservation:
    #FULL TRIANING DICT STRUCTURE: the days in the a day_start key must be consecutive.  IF there is a new season day inbetween, then it should be made into a new check-in key!
    #
    #created_at, end_status: ,checkin, checkout:,
    #tables: date_start: "r_of_i_t":numpy array

    def __init__(self, full_training_dict = None):
        #big class variables
        self.training_data_set = {}
        self.tables = {}
        self.s_of_t = {}
        self.b_hat_i_t = np.zeros( (365, 365) ) #for all year
        self.r_of_i_t = np.zeros( (365, 365) ) #for all year
        if full_training_dict:
            self.add_training(full_training_dict)

        #fill tables
        self.fill_tables()

        #make the trend estimator for every table
        self.this_trend = trend_estimator.TrendEstimator(self.s_of_t)
        #make b_hat_i_t
        self.make_b_hat_i_t()

        #make binomial distribution object, wich must be for whole year
        #non-variable variance for whole data set assumed

        #need to make combined r_i_t for binomial predictor
        self.binomial_distribution = binomial_distribution.BinomialDistribution(self.b_hat_i_t, self.r_of_i_t)


    def make_tables(self, duration_int):
        #one for each season
        dictionary = {}
        dictionary['r_of_i_t'] = np.zeros( (365, duration_int))
        dictionary['c_of_t'] = np.zeros( (1, duration_int)) #just keeps track of % of cancellations that occur for reservations made at t in season
        dictionary['b_hat_i'] = np.zeros( (1, 365) )
        dictionary['r_of_j_t'] = np.zeros( (1, 365) )
        #length_of_stay: {season: duration_length: probability}
        dictionary['length_of_stay'] = {}
        dictionary['season_t_to_year_t_conversion'] = np.zeros( (1, duration_int) ) #the index is the t value in the season, the array value is the value in the full year _ t

        return dictionary


    '''
    THIS IS WRITTEN FOR when the clusters days are ordered by cluster and ARE NOT necessarily consecutive, however it is
    IF this is the table used, it's important that when in prediction, you calculate the day_int of the day in the cluster's individual calendar, or make a calendar dict to keep track.
    '''

    def fill_tables(self):
        #full reservation counts for t
        #week_number: i:count
        #duration_length: count

        #this_cluster of consecutive days: day: reservation_id: reservation_data
        all_checkins = self.tables.keys()

        #fill in tables in order of dates
        sorted_checkins = sorted(all_checkins)
        t_int = 0

        for k_cluster in sorted_checkins:
        #k_cluster_data in self.training_data_set.iteritems():
            all_lengths_of_stays = {}
            k_cluster_data = self.training_data_set[k_cluster]

            if isinstance(k_cluster_data.keys()[0], str):
                sorted_days = sorted([datetime.datetime.strptime(entry, "%Y-%m-%d").date() for entry in k_cluster_data.keys()])
            else:
                sorted_days = sorted([entry for entry in k_cluster_data.keys()]) #preserve date object


            for t, day in enumerate(sorted_days):
                #self.s_of_t[key][day] = 0
                #
                #Life Hack: center s_of_t where 0 = 1 to make time_series prediction happy
                self.s_of_t[k_cluster][day] = 1

                if k_cluster_data[day]:
                    cancellation_count = 0
                    for reservation_id, reservation_data in k_cluster_data[day].iteritems():

                        #get general variables
                        if not isinstance(reservation_data['checkin'], str):
                            t_string = reservation_data['checkin'].strftime("%Y-%m-%d")
                            checkin = reservation_data['checkin']
                        else:
                            t_string = reservation_data['checkin']
                            checkin = datetime.datetime.strptime(reservation_data['checkin'], "%Y-%m-%d").date()


                        if not isinstance(reservation_data["created_at"], str):
                            i_string = reservation_data["created_at"].strftime("%Y-%m-%d")
                            enquiry_day = reservation_data['created_at'].date()
                        else:
                            i_string = reservation_data["created_at"]
                            enquiry_day = datetime.datetime.strptime(reservation_data['created_at'], "%Y-%m-%d").date()


                        i = (datetime.datetime.strptime(reservation_data['checkin'], "%Y-%m-%d").date() - enquiry_day).days

                        if i < 0:
                            print "input wrong for enquiry day in fill_tables_by_cluster"
                            sys.exit()

                        #do duration
                        duration = (datetime.datetime.strptime(reservation_data['checkout'], "%Y-%m-%d").date() - checkin ).days
                        if duration not in all_lengths_of_stays.keys():
                            all_lengths_of_stays[duration] = 1
                        else:
                            all_lengths_of_stays[duration] += 1

                        #increment r_of_j_t, total reservations made regardless
                        self.tables[k_cluster]['r_of_j_t'][0, t] += 1
                        #do reservations and cancellations
                        if reservation_data['status'] == 'CANCELLED':
                             #increments regardless
                            cancellation_count += 1
                        elif reservation_data['status'] == 'CONFIRMED': #constrained demand
                            #fill number of reservations that come on day i for day t.
                            self.s_of_t[k_cluster][day] += 1
                            self.tables[k_cluster]['r_of_i_t'][i, t] += 1
                            self.r_of_i_t[i, (t + t_int)] += 1
                        elif reservation_data['status'] == 'ENQUIRY':
                            #LOOK AT LATER
                            self.tables[k_cluster['r_of_i_t']] += 1

                    #do cancellation, which can only be the generalised cancellation rate, not by i
                    try:
                        self.tables[k_cluster]['c_of_t'][0, t] = float(cancellation_count) / self.tables[k_cluster]['r_of_j_t'][0, t]
                    except ZeroDivisionError:
                        #there was no reservation data for this day
                        #we will keep the cancellation rate of 0
                        pass

                #do b_hat_of_i
                for i in range(0, 365):
                    self.tables[k_cluster]['b_hat_i'][0, i] = self.make_b_hat_i(i, k_cluster)

                t_int = len(sorted_days)

            #do duration_probability
            season_max_count =  sum(all_lengths_of_stays.values())
            for duration_length, count in all_lengths_of_stays.iteritems():
                self.tables[k_cluster]['length_of_stay'][duration_length] = float(count)/season_max_count


    def make_b_hat_i(self, i, key):
        season_length = self.tables[key]['r_of_i_t'].shape[1]
        b_hat_i = float(1)/season_length

        sum_over = 0
        for t in range(0, season_length):
            to_add = self.tables[key]['r_of_i_t'][i, t]
            try:
                sum_over += float(to_add)/self.tables[key]['r_of_j_t'][0, t]
            except ZeroDivisionError:
                #there were no reservations on this day
                #will see a: invalid value encountered in double_scalars
                pass


        return b_hat_i * sum_over

    def make_b_hat_i_t(self):
        all_keys = self.tables.keys()

        if isinstance(all_keys[0], str):
            all_keys = [datetime.datetime.strptime(entry, "%Y-%m-%d").date() for entry in all_keys]

        sorted_keys = sorted(all_keys)

        t_int = 0
        for key in sorted_keys:
            season_length = self.tables[key]['r_of_i_t'].shape[1]
            for t in range(0, season_length):
                #update season to year conversion
                self.tables[key]['season_t_to_year_t_conversion'][0, t] = (t_int + t)

                for i in range(0, 365):
                    b_hat_i_t = self.tables[key]['b_hat_i'][0, i] * self.this_trend.predict_forecasted_s_t(t_int, 0)

                    #TEST
                    if not math.isnan(b_hat_i_t):
                        #print "b_hat_i is nan for t ", t, " i ", i
                        print "WHOOPEE WE GOT SOMETHING" #never get anything
                    else:
                        print "we have nan again"
                        sys.exit()

                    #self.b_hat_i_t[i, t_int] = self.tables[key]['b_hat_i'][0, i] * HACK: self.this_trend.predict_forecasted_s_t(t_int, 1)
                    #for the situation where s_of_t has been normalised around 1, thus the minus 1 later
                    proposed_trend = self.this_trend.predict_forecasted_s_t(t_int, 1) - 1
                    if proposed_trend < 0:
                        proposed_trend = 0

                    self.b_hat_i_t[i, t_int] = self.tables[key]['b_hat_i'][0, i] * proposed_trend

            t_int = season_length


    def discover_season(self, day):
        #figure out where day is in the history
        season_starts = self.tables.keys()
        season_string = False

        if isinstance(season_starts[0], str):
            season_starts = [datetime.datetime.strptime(entry, "%Y-%m-%d").date() for entry in season_starts]
            season_string = True

        if isinstance(day, str):
            day = datetime.datetime.strptime(day, "%Y-%m-%d").date()

        sorted_checkins = sorted(season_starts)

        for x,checkin in enumerate(sorted_checkins):
            if day < checkin:
                if season_string:
                    return sorted_checkins[x-1].strftime("%Y-%m-%d")
                return sorted_checkins[x-1]

        if season_string:
            return sorted_checkins[len(sorted_checkins) - 1].strftime("%Y-%m-%d")

        return sorted_checkins[len(sorted_checkins) - 1]



    '''
    i is the day ahead that we are looking at, to predict for day t
    returns an int number of predicted reservations, minus cancellations
    day can be a datetime object
    '''
    def _predict_reservations(self, day, i):
        season = self.discover_season(day)
        predicted_reservations = 0

        #figure out season_t
        if isinstance(season, str):
            season = datetime.datetime.strptime(season, "%Y-%m-%d").date()
        if isinstance(day, str):
            day = datetime.datetime.strptime(day, "%Y-%m-%d").date()
        season_t = (day - season).days

        #figure out year_t
        year_t = self.tables[season]['season_t_to_year_t_conversion'][0, season_t]

        #randomly gives a n and p from this day's n,p table
        n_p_dict = self.binomial_distribution.get_n_p(i, year_t)

        #in case when there was no reservation data or no chance of the reservation materialising
        if n_p_dict['n'] == 0 or n_p_dict['p'] == 0:
            return 0

        #probability is the probabiliyt that the reservation will materialise for day t, i days in advance
        threshold = int(n_p_dict['p'] * 100)

        for x in range(0, n_p_dict['n']):
            random_pick = randint(1, 100) #includes the ends
            if random_pick < threshold:
                predicted_reservations += 1

        return predicted_reservations

    '''
    **predicted cancellations based on average chance of cancellation for the season**

    returns an int number of predicted cancellations
    predicted_reservations_dict: i : [durations, None]
    '''
    def _predict_cancellations(self, season, t, predicted_reservations_dict):
        cancellation_threshold = int(self.tables['c_of_t'][0, t] * 100)
        predicted_cancellations = 0

        final = {}
        for i, duration_list in enumerate(reservations_i_list):
            for x, duration in enumerate(duration_list):
                cancellation_choice = randint(0, 100)

                #if the chance of being cancelled is 20%, then we say we randomly pick an int from 100 and the int is < than the threshod (20 in this case), then it's a cancellation, and if it's greater the reservation survives
                if cancellation_choice > cancellation_threshold:
                    if i not in final.keys():
                        final[i] = []

                    final[i].append(duration)

        #return dict: {i: [durations]}
        return final

    #t is the day array int in the season
    def _predict_duration(self, season):
        probability_dict = self.tables[season]['length_of_stay'][0, t] #check to make sure there is no off by one error
        probability_thresholds = {} #probability threshold: duration value
        last_threshold = 0
        for length, length_probability in probability_dict.iteritems():
            threshold = last_threshold + (length_probability * 100)
            probability_thresholds[threshold] = length

        choice = randint(1, 101)
        for x, thresholds in enumerate(sorted(probability_thresholds.keys() ) ):
            if choice >= threshold:
                return probability_thresholds[x-1]

        return probability_thresholds[len(probability_thresholds.keys()) - 1]


    '''
    This is the main prediction function
    day can be a datetime object
    original_reservations_dict: day: [i: duration]

    default to predicting at least up to the day before prediction

    '''
    def predict(self, day, day_known_reservations_dict, point_of_view = 0):
        #must be datetime object

        #the key is i before checkin day
        if day_known_reservations_dict:
            tot_reservations_predicted = day_known_reservations_dict
        else:
            tot_reservations_predicted = {}

        for i in range(0, point_of_view):
            proposed_reservations = self.predict_reservations(i, day)
            if proposed_reservations < 0:
                print "we have a negative number of reservations proposed."
                sys.exit()
            elif proposed_reservations > 0:
                for x in range(0, proposed_reservations):
                    if i not in tot_reservations_predicted.keys():
                        tot_reservations_predicted[i] = []

                    tot_reservations_predicted[i].append(None)

        if not tot_reservations_predicted:
            return 0

        #make cancelations
        season = self.discover_season(day)
        season_t = (day - season).days
        final_reservations_dict = self._predict_cancellations(season, season_t, tot_reservations_predicted)

        #make durations
        reservation_dict = {}
        for i, durations_list in final_reservations_dict.iteritems():
            for x, duration in enumerate(durations_list):
                if duration is None:
                    duration = self._predict_duration(season)

        #returns r
        return reservation_dict


    #begin the unit testing portion of this class

'''
pass in the object, and where you expect to see a none-0 value in the r_of_i_of_t
will print stdout if it's good and if it's not
'''
def test_r_ofi_of_t(monte_carlo_object, season, expected_coordinates_of_entry):
    #full_training_dict: season_designation: reservation: created_at, end_status: ,checkin, duration:,

    if monte_carlo_object.r_of_i_t[season][expected_coordinates_of_entry[0], expected_coordinates_of_entry[1]] is not None:
        print "There is a valid entry in r_of_i_of_t for this expectation"
    else:
        print "test of r (i,t) failed"

    #test initiation

def test_r_ofj_t(monte_carlo_object, season, expected_coordinates_of_entry):
    if monte_carlo_object.r_of_j_t[season][expected_coordinates_of_entry[0], expected_coordinates_of_entry[1]] is not None:
        print "This is in s of j, t: ", monte_carlo_object.r_of_j_t[season][expected_coordinates_of_entry[0], expected_coordinates_of_entry[1]]
    else:
        print "test r of j, t failed"

def test():
    #make sample
    with open('../data/sample.json') as jsonFile:
        reservation_dict = json.load(jsonFile)

    for location_id in reservation_dict.keys():
        print "On location ", location_dict[location_id]
        #results: listing_id: results
        results = {}
        for listing_id in training_dict_all[location_id].keys():
            occupancy_predictions = {} #will be filled with arbitrary occupancy dicts where the k iteration is the key

            #(self, full_training_dict = None, k_iterations = 1)
            listing_Monte = MonteCarlo.ModifiedMonteCarlo(training_dict_all[location_id][listing_id])

            for k in range(0, k_iterations):

                #reservations come as dict with int: duration_int
                #this_occupancy_dict: day: i: [duration]
                this_occupancy_dict = get_first_reservations_predictions(start_date, end_date)

                for day in my_time._daterange(start_date, end_date):
                    fill_predictions_occupancy_on_day(myMonte, this_occupancy_dict, day, end_date, k_iterations)

                #this occupancy dict should be like day: binary 0/1
                occupancy_predictions[k] = this_occupancy_dict

            #average the results
            prediction_dict = average_predictions(occupancy_predictions)
            #now do analysis of results for
            listing_results = compare_results(listing_id, prediction_dict)
            results[listing_id] = listing_results

    print "hello"

if __name__ == '__main__':

    test()




