from library import MonteCarlo_new
from library import common_database_functions, my_time, classification
import datetime
import json
import pandas as pd
import timeit
import threading

'''
Every seperate k-means clustered season shall be it's own training set

training_dict needs to be in this format:
training_dict: first checkin_date of the season: all consecutive days in this season cluster

the days in the a day_start key must be consecutive.  IF there is a new season day inbetween, then it should be made into a new check-in key!
'''
'''
inputs is a datetime object

outputs a dictionary with: all reservations known for that day

returns dict: day: i: duration, or dict: day: None for empty days.  Doesn't really change anything because an empty dict still returns False
'''
with open('data/reservation_dict_combined.json') as jsonFile:
    reservation_data = json.load(jsonFile)


def get_first_reservations_predictions(listing_id, first_day_of_testing, last_day_testing, point_of_view = 0):
    global reservation_data
    #day: integer of predicted occupancy, if integer ==1 then occupancy, if integer == 0, then no occupancy
    final = {}

    reservation_dict = reservation_data[listing_id]

    for day in my_time._daterange(first_day_of_testing, last_day_testing):
        final[day] = {}
        if reservation_dict[str(day.year)][str(day)]['reservations']:
            for reservation_id, reservation_data in reservation_dict[str(day.year)][str(day)]['reservations']:

                checkin = datetime.datetime.strptime(reservation_data['checkin'], "%Y-%m-%d").date()
                checkout = datetime.datetime.strptime(reservation_data['checkout'], "%Y-%m-%d").date()
                duration = (checkout - checkin).days
                created_at = datetime.datetime.strptime(reservation_data['created_at'], "%Y-%m-%d").date()
                i = (checkin - created_at).days

                if i >= point_of_view:
                    try:
                        final[day][i].append(duration) #could be that multiple reservations come in on same day
                    except KeyError:
                        final[day][i] = [duration]

    return final


#reservation_dict: occupancy dict predictions for the day, i: [durations predicted]
#best match day idea already folded into the MonteCarlo implementation
def fill_predictions_occupancy_on_day(listing_id, monte_carlo_object,occupancy_dict, reservation_dict, this_day, point_of_view = 0):

    #is a list, full of dicts: {i:duration}
    possible_reservations = monte_carlo_object.predict(this_day, reservation_dict[this_day], point_of_view)

    if possible_reservations:
        #take the earliest reservation
        earliest_i = sorted(possible_reservations.keys()[0]
        longest_duration = max(possible_reservations[earliest_i])

        #if the first day of the reservation hasn't been made, take that reservation
        #Do not count the day of checkout
        for day in my_time._daterange(this_day, this_day + datetime.timedelta(longest_duration - 1)):
                occupancy_dict[day] = 1


'''
expecting structure to be:
method: listing_ids: full results
'''
def results_averaging(final_results_dict):
    '''
    "true_true", "true_false":, false_false": , "false_true":, "occupancy_precision", "empty_precision", "correct_overall",  "occupancy_recall", "empty_recall", "occupancy_fOne", "empty_fOne", }
    '''
    results_store = {}
    for listing_ids, full_data in final_results_dict.iteritems():
        if full_data:
            for result_type in ["occupancy_precision", "empty_precision", "occupancy_recall", "empty_recall", "occupancy_fOne", "empty_fOne"]:
                if result_type not in results_store[method].keys():
                        results_store[method][result_type] = []

                if full_results[result_type]:
                    results_store[result_type].append(full_results[result_type])
                else: #if the result was None or 0
                #often because there weren't many occupancies or falses in a test set
                    print "didn't have good data here"
                    print listing_ids
                    pass

    #get the average
    final = {}

    for result_type, tot_in_list in result_type_data.iteritems():
        if len(tot_in_list) > 0:
            final[method][result_type] = float(sum(tot_in_list))/len(tot_in_list)
        else:
            final[method][result_type] = None

    return final

#occupancy_prediction: K_iterations : {day:}
#make sure that the list adds predictions in day order.
def calculate_results(listing_id, occupancy_predictions_dict):
    global reservation_data
    #make the average results first and find true results
    #always have a k = 0
    sorted_days = [entry for entry in occupancy_predictions_dict[0].keys()]

    average_results = []
    true_results = []
    for day in sorted_days:
        all_predictions = [occupancy_predictions_dict[k][day] for k in occupancy_predictions_dict.keys()]
        this_average = float(sum(all_predictions))/len(all_predictions)
        if this_average >= 0.5:
            to_add = 1
        else:
            to_add = 0

        average_results.append(to_add)
        true_results.append(occupancy_dict[str(listing_id)][str(day.year)][str(day)])

    #compare
    these_results = classification.results(prediction_list, classification)

    return these_results.get_results()


'''
Makes the trianing dict for the monte carlo object with a year of data following the point of view
'''

def one_k_prediction(my_monte_object, prediction_start, prediction_end, point_of_view):

    #reservations come as dict with int: duration_int
    #this_occupancy_dict: day: i: [duration]
    predicted_reservations_dict = get_first_reservations_predictions(listing_id, start_date, end_date, point_of_view)

    #TEST
    occupancy_dict = {start_date: 1}

    for day in my_time._daterange(prediction_start, prediction_end):
        try:
            if occupancy_dict[day] == 1:
                #skip prediction if this day is already predicted for
                break
        except KeyError:
            occupancy_dict[day] = 0

        #NEED TO MAKE START_DATE
        if point_of_view_day > datetime.date(2015, 1, 1):
            start_date = point_of_view_day - datetime.timedelta(365)
        else:
            start_date = datetime.date(2014, 1, 1)

        if my_monte is False:
            return False

        fill_predictions_occupancy_on_day(listing_id, my_montes[day], occupancy_dict, predicted_reservations_dict[day], day, point_of_view)

    return this_occupancy_dict

'''
date inputs can be datetime objects

k_iterations: the prediction will be run the number of k-iterations, and the results are averaged across

training_dict_all will have data for all two years of data, 2014- 2016

point_of_view must be the datetime date object
'''
def single_listing_prediction(experiment_name, start_date, end_date, k_iterations = 1, point_of_view = 0):
    global reservation_data, point_of_view
    #set up training dict for single listing predictions

    location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}
    all_results = {}
    for location_id in ['0', '1', '19']:
        print "On location ", location_dict[int(location_id)]
        #results: listing_id: results
        results = {}

        testing_listings = common_database_functions.get_listings_for_location(int(location_id))
        testing_start = datetime.date(2015, 1, 1)
        testing_end = datetime.date(2016, 1, 30)

        for listing_id in testing_listings:

            occupancy_predictions = {} #will be filled with arbitrary occupancy dicts where the k iteration is the key
            try:
                #testing_start, testing_end, full_training_dict = None, point_of_view = 0)
                my_monte_defined = MonteCarlo_new.ModifiedMonteCarlo_Base(start_date, end_date, reservation_data[str(listing_id)], point_of_view)

            except KeyError:
                #this listing is not available for analysis
                continue

            #do k_iterations
            for k in xrange(0, k_iterations, 1):
                occupancy_prediction[k] = one_k_prediction(my_monte_defined, start_date, end_date, point_of_view)

                if occupancy_prediction[k] is False:
                    print "This listing didn't have good data, ", listing_id
                    break

            #get results
            if occupancy_predictions:
                results[listing_id] = calculate_results(listing_id, occupancy_predictions)

        location_dict = {1: "Barcelona", 0: "Rome", 19: "Rotterdam"}
        '''
        do results analysis
        results: id: {scores: values} where scores are confusion matrix and
        '''
        classification.save_to_database("monte_carlo_individual_results", experiment_name, location_dict[location_id], results)

        all_results[location_dict[location_id]] = results_averaging(results)
        classification.save_to_database("monte_carlo_average_results", experiment_name, location_dict[location_id], all_results)

        print analysis
        print "analyzed ", len(results), "records"
    print "finished"


def main():

    #experiment 1 (BASELINE BEST), predict from point of view = 0 (for the same day)
    #
    single_listing_prediction("point-0 one year prediction", datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 10) #to match machine learning

    #experiment 2, point of view for one week before
    single_listing_prediction('point_1 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 10, point_of_view = 1)

    #experiment 4
    single_listing_prediction('point_3 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 10, point_of_view = 3)

    single_listing_prediction('point_7 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 10, point_of_view = 1)

    #one month ahead
    single_listing_prediction('point_30 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 10, point_of_view = 30)

    #2 months ahead
    single_listing_prediction('point_60 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 10, point_of_view = 60)

    #3 months ahead
    single_listing_prediction('point_90 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 10, point_of_view = 90)

    print "hello"

if __name__ == '__main__':
    main()
