import json
from library import my_time, common_database_functions, database
import datetime

with open("data/monte_carlo_reservation_dict.json") as jsonFile:
        all_reservations_dict = json.load(jsonFile)

with open('data/k-means_season_clusters.json') as jsonFile:
    k_means = json.load(jsonFile)
with open ('data/occupancy_dict.json') as jsonFile:
    occupancy_dict = json.load(jsonFile)

listing_location = common_database_functions.location_listing_pairings(True)

#final: listing_id: day: {reservations: {}, k_cluster: , occupancy: }
final = {}

#find valid listings with the right created-at dates
worldhomes_data = database.database("worldhomes")
enough_data_listings = worldhomes_data.get_data("SELECT `id` FROM `listings` WHERE `created_at` > '2013-12-31';")
enough_data_listings = [entry[0] for entry in enough_data_listings]

valid_ids = [this_id for this_id in occupancy_dict.keys() if int(this_id) in enough_data_listings]

for listing_id in valid_ids:
    final[listing_id] = {}
    for day in my_time._daterange(datetime.date(2014, 1, 1) , datetime.date(2016, 1,30) ): #does not include the outer bound
        year = str(day.year)

        final[listing_id][str(day)] = {}
        try:
            if all_reservations_dict[listing_id][year][str(day)]:
                final[listing_id][str(day)]['reservations'] = all_reservations_dict[listing_id][year][str(day)]
            else:
                final[listing_id][str(day)]['reservations'] = None
        except KeyError:
            del final[listing_id]
            break

        final[listing_id][str(day)]['occupancy'] = occupancy_dict[listing_id][year][str(day)]
        final[listing_id][str(day)]['k_cluster'] = k_means[year][str(listing_location[int(listing_id)])]['3'][str(day)]

with open('data/reservation_dict_combined.json', 'w') as jsonFile:
    json.dump(final, jsonFile)
