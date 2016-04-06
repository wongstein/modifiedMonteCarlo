import database
import datetime
'''
if the input is a list, the output is a dictionary where the the key is the location id and the value is a list of all listing_ids assocated

if not, then just a list is outputed
'''
def get_listings_for_location(location_id):
    #return listings that have at least one year of occupancy data
    #And restricted to barcelona

    if isinstance(location_id, list):
        final = {}
        for this_location in location_id:
            final[this_location] = get_listings_for_single_location(this_location)

        return final
    else:
        return get_listings_for_single_location(location_id)

def get_listings_for_single_location(location_id):
    testing_listings = []
    thesis_data = database.database("Thesis")

    query = "SELECT `listing_locations_DBSCAN_final`.`listing_id` FROM `listing_locations_DBSCAN_final` WHERE `label_id` = %s;"

    initial_data = thesis_data.get_data(query % location_id)

    thesis_data.destroy_connection()
    return [entry[0] for entry in initial_data]

def get_id_location_pairs():

    thesis_data = database.database("Thesis")
    pairs = data_thesis.get_data("SELECT `listing_clusters_plain`.`listing_id`,`listing_locations_DBSCAN_final`.`label_id`, `listing_clusters_plain`.`cluster_id` FROM `listing_clusters_plain` INNER JOIN `listing_locations_DBSCAN_final` ON `listing_locations_DBSCAN_final`.`listing_id` = `listing_clusters_plain`.`listing_id` WHERE label_id != -1;")
    thesis_data.destroy_connection()

    return pairs

'''
types wanted is a list
'''
def get_reservations(types_wanted):
    worldhomes_data = database.database("worldhomes")

    query = "SELECT `listing_id`,`checkin`, `checkout`, `status`, CASE status WHEN 'CONFIRMED' OR 'BLOCKEDBYCONFIRMED' OR 'CANCELLATIONREQUESTED' OR 'UNAVAILABLE' OR 'DOUBLEBOOKING' THEN 'CONFIRMED' END AS status FROM `reservations` WHERE `additional_description` NOT LIKE 'test ' AND `checkin` >= '2014-01-01' AND `checkout` < '2016-01-30' AND `listing_id` IS NOT NULL AND DATEDIFF(`checkin`, `created_at`) <= 365 AND DATEDIFF(`checkout`, `checkin`) >= 0 ORDER BY `status`;"

    reservations = worldhomes_data.get_data(query)

    worldhomes_data.destroy_connection()

    return reservation

'''
if dict is true, then the data is returned as a dict where listing_id is the key and the location is the value
'''
def location_listing_pairings(return_dict = False):

    thesis_data = database.database("Thesis")

    pairing_list = thesis_data.get_data("SELECT `listing_id`, `label_id` FROM `listing_locations_DBSCAN_final`;")
    if return_dict:
        return {entry[0]:entry[1] for entry in pairing_list}
    else:
        return pairing_list

    thesis_data.destroy_connection()

def listing_cluster_type_pairings(return_dict = True):

    thesis_data = database.database("Thesis")

    pairing_list = thesis_data.get_data("SELECT * FROM `listing_clusters_plain`;")

    return {entry[0]: entry[1] for entry in pairing_list}

def get_earliest_dates(as_dict = False):
    worldhomes_data = database.database("worldhomes")

    data_list = worldhomes_data.get_data("SELECT `id`, `created_at` FROM `listings`;")

    worldhomes_data.destroy_connection()

    if as_dict:
        this_dict = {entry[0]: datetime.datetime.strptime(entry[1], "%Y-%m-%d") for entry in data_list}
        return this_dict
    else:
        return data_list

