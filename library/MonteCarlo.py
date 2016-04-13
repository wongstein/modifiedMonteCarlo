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

    def __init__(self, full_training_dict = None):
        #big class variables
        training_length = len(full_training_dict.keys())

        #top row is the value
        #second is the weekday designation
        self.s_of_t = np.zeros( (3, training_length) )
        self.r_i_t = np.zeros( (365, training_length) )
        self.r_j_t = np.zeros( (1, training_length) )
        #self.r_i_t_over_r_j_t = np.zeros( (365, training_length) )
        self.c_of_t = np.zeros( (1, training_length) )

        self.durations_of_t = np.zeros((training_length, 15))

        self.day_int_conversion = {}
        self.season_day_tracker = {0:[], 1:[], 2:[]}

        self.fill_global_tables(full_training_dict)


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

        season_stay_lengths = {0:{}, 1:{}, 2:{}}
        for t, day in enumerate(sorted_days):
            season = int(training_data_set[str(day)]['k_cluster'])
            #day: "season": , "t":
            self.day_int_conversion[day] = t
            self.season_day_tracker[season].append(day)

            #Life Hack: center s_of_t where 0 = 1 to make time_series prediction happy
            self.s_of_t[0, t] = 1
            self.s_of_t[1, t] = day.weekday()
            self.s_of_t[2, t] = season

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



#begin the unit testing portion of this class


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
