from monte_carlo import MonteCarlo
from library import common_database_functions, my_time, classification
import datetime
import json

'''
Every seperate k-means clustered season shall be it's own training set

training_dict needs to be in this format:
training_dict: first checkin_date of the season: all consecutive days in this season cluster

the days in the a day_start key must be consecutive.  IF there is a new season day inbetween, then it should be made into a new check-in key!
'''
training_dict_all = {}
with open("data/monte_carlo_reservation_dict.json") as jsonFile:
        all_reservations = json.load(jsonFile)

with open("data/occupancy_dict.json") as jsonFile:
    occupancy_dict = json.load(jsonFile)

#BASED ON PER LISTING TRAINING
def make_training_dict_structure():
    #location_id: listing_id: k_cluster_checkin: day: reservation data
    global training_dict_all

    #location: k_means_type: day: classification
    with open("data/k-means_season_clusters.json") as jsonFile:
        all_k_means_data = json.load(jsonFile)

    #goal: to group the trianin data so that each cluster is a consecutive span of days
    for location in [0, 1, 19]:
        training_dict_all[location] = {}
        valid_ids = common_database_functions.get_listings_for_single_location(location)
        for listing_id in valid_ids:
            training_dict_all[location][listing_id] = {}
            this_dict = training_dict_all[location][listing_id]

            #should be a year, convert to datetime objects, then sort
            original_days = [datetime.datetime.strptime(entry, "%Y-%m-%d") for entry in all_k_means_data['2014'][str(location)]['3'].keys()]
            sorted_days = sorted(original_days)

            #setup loop
            last_key = sorted_days[0]
            training_dict_all[location][listing_id][last_key] = {}

            #output: training_dict_all: location: first_day: day: {}
            for x, day in enumerate(sorted_days):
                if all_k_means_data['2014'][str(location)]['3'][day.strftime("%Y-%m-%d")] == all_k_means_data['2014'][str(location)]['3'][last_key.strftime("%Y-%m-%d")]: #if the keys are the same
                    training_dict_all[location][listing_id][last_key][day] = {} #will hold all reservations later
                else:
                    last_key = day #update
                    training_dict_all[location][listing_id][last_key] = {day:{}}

def fill_training_dict_with_reservations():
    global training_dict_all, all_reservations

    '''
    #all_reservations: location_id:year: day:reservations
    for location_id in [0, 1, 19]:
        listing_ids = common_database_functions.get_listings_for_location(location_id)
        valid_ids = [this_id for this_id in listing_ids if str(this_id) in all_reservations.keys()]
        for listing in valid_ids:
            for checkin, k_data in training_dict_all[location_id].iteritems():
                for day, dictionary in k_data.iteritems():
                    if all_reservations[str(listing)][str(day.year)][str(day.date())]:

                        for reservation, reservation_data in all_reservations[str(listing)][str(day.year)][str(day.date())].iteritems():
                            dictionary[reservation] = reservation_data
    '''
    for location_id, all_listing_ids in training_dict_all.iteritems():
        for listing_id, k_seasons_data in all_listing_ids.iteritems():
            if not str(listing_id) in all_reservations.keys():
                continue

            for checkin, k_data in training_dict_all[location_id].iteritems():
                for day, dictionary in k_data.iteritems():
                    if all_reservations[str(listing_id)][str(day.year)][str(day.date())]:

                        for reservation, reservation_data in all_reservations[str(listing_id)][str(day.year)][str(day.date())].iteritems():
                            dictionary[reservation] = reservation_data

'''
input is a datetime object
'''
def get_first_reservations_predictions(listing_id, first_day_of_testing, last_day_testing):
    global all_reservations
    #day: integer of predicted occupancy, if integer ==1 then occupancy, if integer == 0, then no occupancy
    final = {day: 0 for day in my_time._daterange(first_day_of_testing, last_day_testing)}
    reservation_dict = all_reservations[listing_id]

    for day in final.keys():
        if reservation_dict[day.strftime("%Y-%m_%d")]: #if there are reservations for this day
            for reservation_id, reservation_dict in reservation_dict[day.strftime("%Y-%m_%d")]:
                created_at = datetime.datetime.strptime(reservation_dict['created_at'], "%Y-%m-%d").date()
                if (first_day_of_testing - created_at).days() >= 0 and reservation_dict['status'] != 'CANCELLED': #must do cancelled here, sorry
                    checkout = datetime.datetime.strptime(reservation_dict['checkout'], "%Y-%m-%d").date()
                    checkin = datetime.datetime.strptime(reservation_dict['checkin'], "%Y-%m-%d").date()
                    for duration_day in my_time._daterange(checkin, checkout):
                        final[duration_day] += 1

    return final

#occupancy_dict: #int: duration
def make_predictions_for_single_day(monte_carlo_object, occupancy_dict, this_day, end_date):

    possible_reservations = monte_carlo_object.predict_reservations(this_day)

    if possible_reservations:
        take_max = max(possible_reservations.values())
        #if the first day of the reservation hasn't been made, take that reservation
        if not occupancy_dict[day]:
            for day in my_time._daterange(this_day, this_day + datetime.timedelta(take_max)):
                occupancy_dict[day] = 1


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

def single_listing_prediction(start_date, end_date):
    global training_dict_all
    #set up training dict for single listing predictions
    make_training_dict_structure()
    fill_training_dict_with_reservations()


    for location_id in training_dict_all.keys():
        #results: listing_id: results
        results = {}
        for listing_id in training_dict_all[location_id].keys():
            myMonte = MonteCarlo.ModifiedMonteCarlo(training_dict_all[location_id][listing_id], 2)

            #reservations come as dict with int: duration_int
            this_occupancy_dict = get_first_reservations_predictions(start_date, end_date)
            for day in my_time._daterange(start_date, end_date):
                make_predictions_for_single_day(myMonte, this_occupancy_dict, day, end_date)

            #now do analysis of results for
            listing_results = compare_results(listing_id, prediction_dict)
            results[listing_id] = listing_results

def main():
    global training_dict_all, all_reservations



    #experiment 1, point of view from the immediate end of training, predict one year in advance
    single_listing_prediction(datetime.datetime(2015, 1, 1), (2015, 12, 31))

    print "hello"

if __name__ == '__main__':
    main()
