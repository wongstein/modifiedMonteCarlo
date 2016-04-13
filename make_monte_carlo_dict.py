import json
from library import my_time, common_database_functions
import datetime

training_dict_all = {}

with open("data/monte_carlo_reservation_dict.json") as jsonFile:
        all_reservations = json.load(jsonFile)

with open("data/occupancy_dict.json") as jsonFile:
    occupancy_dict = json.load(jsonFile)

#BASED ON PER LISTING TRAINING
#ALso, delete listings whos created dates are not before 2014- 01- 01

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

            #should be a year, convert to datetime objects, then sort
            for year in ['2014', '2015']:

                #changed dictionary logic
                #group k-clusters together :/
                for day in my_time._daterange(datetime.date(int(year), 1, 1), datetime.date(int(year) + 1, 1, 1)):
                    day_season = all_k_means_data[year][str(location)]['3'][str(day)]
                    if day_season not in training_dict_all[location][listing_id].keys():
                        training_dict_all[location][listing_id][day_season] = {}

                    training_dict_all[location][listing_id][day_season][str(day)] = {}

                '''
                #setup loop
                last_key = sorted_days[0]
                training_dict_all[location][listing_id][str(last_key)] = {}

                #output: training_dict_all: location: first_day: day: {}
                for x, day in enumerate(sorted_days):
                    if all_k_means_data[year][str(location)]['3'][day.strftime("%Y-%m-%d")] == all_k_means_data[year][str(location)]['3'][last_key.strftime("%Y-%m-%d")]: #if the keys are the same
                        training_dict_all[location][listing_id][str(last_key)][str(day)] = {} #will hold all reservations later
                    else:
                        last_key = day #update
                        training_dict_all[location][listing_id][last_key.strftime("%Y-%m-%d")] = {day.strftime("%Y-%m-%d"):None}
                '''

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

            for k_cluster, day_data in k_seasons_data.iteritems():
                for day, dictionary in day_data.iteritems():
                    this_day = datetime.datetime.strptime(day, "%Y-%m-%d").date()
                    if all_reservations[str(listing_id)][str(this_day.year)][str(this_day)]:

                        dictionary = all_reservations[str(listing_id)][str(this_day.year)][str(this_day)]

def main():
    global training_dict_all
    make_training_dict_structure()
    fill_training_dict_with_reservations()

    with open('data/training_dict.json', 'w') as outFile:
        json.dump(training_dict_all, outFile)

if __name__ == '__main__':
    main()

