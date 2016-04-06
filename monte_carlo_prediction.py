from library import MonteCarlo
from library import common_database_functions, my_time, classification
import datetime
import json

'''
Every seperate k-means clustered season shall be it's own training set

training_dict needs to be in this format:
training_dict: first checkin_date of the season: all consecutive days in this season cluster

the days in the a day_start key must be consecutive.  IF there is a new season day inbetween, then it should be made into a new check-in key!
'''

with open("data/training_dict.json") as jsonFile:
        training_dict_all = json.load(jsonFile)
with open("data/monte_carlo_reservation_dict.json") as jsonFile:
        all_reservations = json.load(jsonFile)

monte_objects = {}

def make_monte_objects():
    global monte_objects

    for listing_id, all_data in training_dict_all.iteritems():
        monte_objects[listing_id] = MonteCarlo.ModifiedMonteCarlo(training_dict_all[location_id][listing_id])

'''
inputs is a datetime object

outputs a dictionary with: all reservations known for that day

returns dict: day: i: duration
'''
def get_first_reservations_predictions(listing_id, first_day_of_testing, last_day_testing, point_of_view = 0):
    global all_reservations
    #day: integer of predicted occupancy, if integer ==1 then occupancy, if integer == 0, then no occupancy
    final = {day: 0 for day in my_time._daterange(first_day_of_testing, last_day_testing)}

    reservation_dict = all_reservations[listing_id]

    for day in final.keys():
        if reservation_dict[str(day.year)][str(day)]:
            final[day] = {}
            for reservation_id, reservation_data in reservation_dict[str(day.year)][str(day)]:
                checkin = datetime.datetime.strptime(reservation_data['checkin'], "%Y-%m-%d").date()
                checkout = datetime.datetime.strptime(reservation_data['checkout'], "%Y-%m-%d").date()
                duration = (checkout - checkin).days
                created_at = datetime.datetime.strptime(reservation_data['created_at'], "%Y-%m-%d").date()
                i = (checkin - created_at).days

                if i >= point_of_view:
                    final[day][i] = [duration] #could be that multiple reservations come in on same day

    return final

#occupancy_dict:
def fill_predictions_occupancy_on_day(monte_carlo_object, reservation_dict, this_day, point_of_view = None):

    #if there's already an occupancy, can't take a new reservation
    if reservation_dict[day]:
        return

    #is a list, full of dicts: {i:duration}
    possible_reservations = monte_carlo_object.predict(this_day, reservation_dict[this_day], point_of_view)

    if possible_reservations:
        #take the earliest reservation
        earliest_i = [possible_reservations.keys()][:-1] #take the last one
        longest_duration = max(possible_reservations[earliest_i])

        #if the first day of the reservation hasn't been made, take that reservation
        for day in my_time._daterange(this_day, this_day + datetime.timedelta(longest_duration)):
                reservation_dict[day] = 1


#for today, predict number of cancellations
def compare_results(listing_id, prediction_dict):
    global occupancy_dict

    classification_dict = occupancy_dict[listing_id]
    classification = []
    prediction = []
    for day in prediction_dict.keys(): #day here is going to be datetime.
        if prediction_dict[day] >= 1 :
            prediction.append(1)
        elif prediction_dict[day] <= 0:
            prediction.append(0)

        day_string = day.strftime("%Y-%m_%d")
        if classification_dict[day_string] >= 1:
            classification.append(1)
        elif prediction_dict[day_string] <= 0:
            classification.append(0)

    this_result = classification.results(prediction, classification)
    return this_result.get_results()

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

#occupancy_prediction: K : 0/1
def average_predictions(occupancy_predictions):
    final = {entry: 0 for entry in occupancy_predictions[occupancy_predictions.keys()[0]].keys()}
    for k in occupancy_predictions.keys():


'''
date inputs can be datetime objects

k_iterations: the prediction will be run the number of k-iterations, and the results are averaged across

training_dict_all will have data for all two years of data, 2014- 2016

point_of_view must be the datetime date object
'''
def single_listing_prediction(start_date, end_date, k_iterations = 1, point_of_view = None):
    global training_dict_all
    #set up training dict for single listing predictions

    location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}
    all_results = {}
    for location_id in training_dict_all.keys():
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

        location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}
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
    global training_dict_all, all_reservations

    #could be too data intensive
    #make_monte_objects()

    #experiment 1, point of view from the immediate end of training, predict one year in advance, with just one k-iteration for debugging
    single_listing_prediction(datetime.datetime(2015, 1, 20), (2016,1, 20), 1) #to match machine learning

    print "hello"

if __name__ == '__main__':
    main()
