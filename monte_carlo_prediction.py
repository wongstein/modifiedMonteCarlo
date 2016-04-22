from library import MonteCarlo_new
from library import common_database_functions, my_time, classification
import datetime
import json
import pandas as pd
import time
from multiprocessing import Process, Queue

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

with open('data/occupancy_dict.json') as jsonFile:
    occupancy_dict = json.load(jsonFile)

start_date = None
end_date = None
point_of_view = None

def get_first_reservations_predictions(listing_id, first_day_of_testing, last_day_testing, point_of_view = 0):
    global reservation_data
    #day: integer of predicted occupancy, if integer ==1 then occupancy, if integer == 0, then no occupancy
    final = {}

    reservation_dict = reservation_data[str(listing_id)]

    for day in my_time._daterange(first_day_of_testing, last_day_testing):
        final[day] = {}
        if reservation_dict[str(day)]['reservations']:
            for reservation_id, reservation in reservation_dict[str(day)]['reservations'].iteritems():

                checkin = datetime.datetime.strptime(reservation['checkin'], "%Y-%m-%d %H:%M:%S").date()
                checkout = datetime.datetime.strptime(reservation['checkout'], "%Y-%m-%d %H:%M:%S").date()
                duration = (checkout - checkin).days
                created_at = datetime.datetime.strptime(reservation['created_at'], "%Y-%m-%d %H:%M:%S").date()
                i = (checkin - created_at).days

                if i >= point_of_view:
                    try:
                        final[day][i].append(duration) #could be that multiple reservations come in on same day
                    except KeyError:
                        final[day][i] = [duration]

    return final


#reservation_dict: occupancy dict predictions for the day, i: [durations predicted]
#best match day idea already folded into the MonteCarlo implementation
'''
logic:
'''
def fill_predictions_occupancy_on_day(listing_id, monte_carlo_object,occupancy_dict, reservation_dict_day, this_day):

    #is a list, full of dicts: {i:duration}
    possible_reservations = monte_carlo_object.predict(this_day, reservation_dict_day)

    if possible_reservations:
        #take the earliest reservation
        earliest_i = sorted(possible_reservations.keys())[0]
        longest_duration = max(possible_reservations[earliest_i])

        #if the first day of the reservation hasn't been made, take that reservation
        #Do not count the day of checkout
        for day in my_time._daterange(this_day, this_day + datetime.timedelta(longest_duration)):
                occupancy_dict[day] = 1

'''
expecting structure to be:
 id: {scores: values}
'''
def results_averaging(final_results_dict):
    '''
    "true_true", "true_false":, false_false": , "false_true":, "occupancy_precision", "empty_precision", "correct_overall",  "occupancy_recall", "empty_recall", "occupancy_fOne", "empty_fOne", }
    '''
    results_store = {}
    final = {}

    for listing_ids, results_dict in final_results_dict.iteritems():
        if not results_dict:
            continue
        for result_type, value in results_dict.iteritems():
            try:
                if value is not None:
                    results_store[result_type].append(value)
            except KeyError:
                final[result_type] = None
                results_store[result_type] = [value]
    #get the average

    for result_type, tot_in_list in results_store.iteritems():
        if len(tot_in_list) > 0:
            final[result_type] = float(sum(tot_in_list))/len(tot_in_list)
        else:
            final[method][result_type] = None

    return final

#occupancy_prediction: K_iterations : {day:}
#make sure that the list adds predictions in day order.
def calculate_results(listing_id, occupancy_predictions_dict, start_date, end_date):
    global reservation_data, occupancy_dict

    average_results = []
    true_results = []

    #occupancy_prediction: k: day
    occupancy_prediction_sums = {}
    for k in occupancy_predictions_dict.keys():
        for day in my_time._daterange(start_date, end_date):
            try:
                occupancy_prediction_sums[day].append(occupancy_predictions_dict[k][day])
            except KeyError:
                occupancy_prediction_sums[day] = [occupancy_predictions_dict[k][day]]

    for day, occupancy_list in occupancy_prediction_sums.iteritems():
        average = float(sum(occupancy_list))/len(occupancy_list)

        if average >= 0.5:
            average = 1
        else:
            average = 0

        average_results.append(average)
        true_results.append(occupancy_dict[str(listing_id)][str(day.year)][str(day)])

    #compare
    these_results = classification.results(average_results, true_results)

    return these_results.get_results()


'''
Makes the trianing dict for the monte carlo object with a year of data following the point of view
'''

def one_k_prediction(listing_id, my_monte_object, prediction_start, prediction_end, point_of_view):

    #reservations come as dict with int: duration_int, show's all reservations that are known before the point of view for day (key)
    predicted_reservations_dict = get_first_reservations_predictions(listing_id, prediction_start, prediction_end, point_of_view)

    #this_occupancy_dict: day: i: [duration]
    occupancy_dict = {}

    for day in my_time._daterange(prediction_start, prediction_end):
        try:
            if occupancy_dict[day] == 1:
                #skip prediction if this day is already predicted for
                continue
        except KeyError:
            occupancy_dict[day] = 0

        fill_predictions_occupancy_on_day(listing_id, my_monte_object, occupancy_dict, predicted_reservations_dict[day], day)

    return occupancy_dict


def one_listing_year_prediction(listing_id, listing_reservation_data, start_date, end_date, point_of_view, q):
    occupancy_prediction = {} #will be filled with arbitrary occupancy dicts where the k iteration is the key

    try:
        my_monte_defined = MonteCarlo_new.ModifiedMonteCarlo(listing_id, start_date, end_date, listing_reservation_data, point_of_view)

    except KeyError:
        #this listing is not available for analysis
        return

    #do k_iterations
    for k in xrange(0, 100, 1):
        occupancy_prediction[k] = one_k_prediction(listing_id, my_monte_defined, start_date, end_date, point_of_view)

        if occupancy_prediction[k] is False:
            print "This listing didn't have good data, ", listing_id
            break

    #get results, which returns a tuple: (listing_id, confusion matrix)
    if occupancy_prediction:
        these_results = calculate_results(listing_id, occupancy_prediction, start_date, end_date)
        #print "on listing ", listing_id, " with: ", these_results
        q.put((listing_id, these_results))

'''
date inputs can be datetime objects

k_iterations: the prediction will be run the number of k-iterations, and the results are averaged across

training_dict_all will have data for all two years of data, 2014- 2016

point_of_view must be the datetime date object
'''
def single_listing_prediction(experiment_name, start, end, k_iterations = 1, PofV = 0):
    global reservation_data


    #set up training dict for single listing predictions

    location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}
    all_results = {}
    for location_id in ['0', '1', '19']:
        results = {}
        print "On location ", location_dict[int(location_id)], " point of view: ", point_of_view

        testing_listings = common_database_functions.get_listings_for_location(int(location_id))

        testing_listings = [entry for entry in testing_listings if str(entry) in reservation_data.keys()]

        start_time = time.time()

        #get stuff ready for multi processing
        listing_chunks = []
        processes = 5
        for x in xrange(0, len(testing_listings), processes):
            small_chunk = []
            for y in xrange(0, processes, 1):
                try:
                    small_chunk.append(testing_listings[x + y])
                except IndexError: #then it's finished
                    listing_chunks.append(small_chunk)
                    continue
            listing_chunks.append(small_chunk)

        results = {}
        for id_chunk in listing_chunks:
            #one_listing_year_prediction(results, listing_id)
            #
            #sadly seems that passing in a dict does not work, must use process queue
            q = Queue()
            process_list = []

            start_time = time.time()
            for listing_id in id_chunk:
                p = Process(target = one_listing_year_prediction, args = (listing_id, reservation_data[str(listing_id)], start, end, PofV, q))
                process_list.append(p)
                p.start()

            for process_tuple in process_list:
                return_tuple = q.get()
                results[return_tuple[0]] = return_tuple[1]
                process_tuple.join()

        #for the last straggling process, I can't see them being more than 3 seconds behind
        classification.save_to_database("monte_carlo_individual_results", experiment_name, location_dict[int(location_id)], results)

        all_results[location_dict[int(location_id)]] = results_averaging(results)

        classification.save_to_database("monte_carlo_average_results", experiment_name, location_dict[int(location_id)], all_results[location_dict[int(location_id)]])

        print all_results[location_dict[int(location_id)]]
        print "analyzed ", len(results), "records"
    print "finished"


def main():

    #experiment 1 (BASELINE BEST), predict from point of view = 0 (for the same day)
    #
    single_listing_prediction("point-0 one year prediction", datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 100) #to match machine learning

    #experiment 2, point of view for one week before
    single_listing_prediction('point_1 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 100, PofV = 1)

    #experiment 4
    single_listing_prediction('point_3 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 100, PofV = 3)

    single_listing_prediction('point_7 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 100, PofV = 7)

    #one month ahead
    single_listing_prediction('point_30 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 100, PofV = 30)

    #2 months ahead
    single_listing_prediction('point_60 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 100, PofV = 60)

    #3 months ahead
    single_listing_prediction('point_90 one year prediction', datetime.date(2015, 1, 20), datetime.date(2016,1, 20), k_iterations = 100, PofV = 90)

if __name__ == '__main__':
    main()
