from holtwinters import estimator, holtwinters
import datetime
import numpy as np

'''
this is a helper class to make the the trend estimator for the Modified MonteCarlo
'''

class TrendEstimator():
    #input: (in day order:) check_in: day: s(t), day: s(t), check-IN...
    def __init__(self, s_of_t_dict):
        self.last_day_training = datetime.date(2014, 12, 31) #stupidly early
        #data processing:
        self.make_s_of_t_matrix(s_of_t_dict)
        self.make_deseasonalised_tables()
        #order of deseasonalisation:
        #divide s of t by it's season average
        s_des1_1 = self.de_season(self.s_of_t_matrix[0,:], self.season_averages)

        #take out week averages
        #input: key, week_counter= [s_des1, s_des2]
        s_prime_t = self.de_season(s_des1_1, self.week_averages)

        #take out day averages
        self.s_des_t = self.de_season(s_prime_t, self.day_of_week_averages)

        #make holtwinters, hacked it to have just 2 equal seasons, which after deseasonalisation doesn't exit.  But okay
        self.holtwinters_object = holtwinters.HoltWintersEstimator(self.s_des_t, 3, len(self.s_des_t)/3)
        #self.holtwinters_object = holtwinters.HoltWintersEstimator(self.s_des_t, 1, len(self.s_des_t))

    def make_s_of_t_matrix(self, s_of_t_dict):
        self.s_of_t_matrix = np.zeros( (3, len(s_of_t_dict[s_of_t_dict.keys()[0]]) ) )
        x = 0
        key_counter = -1

        for key, day_data in s_of_t_dict.iteritems():
            key_counter += 1
            sorted_days = sorted(day_data.keys())
            #see if we can find last day
            if sorted_days[len(sorted_days) - 1] > self.last_day_training:
                self.last_day_training = sorted_days[len(sorted_days) - 1]

            key_int = 0
            for day in sorted_days:
                self.s_of_t_matrix[0, x] = day_data[day] #s_of_t

                self.s_of_t_matrix[1, x] = key_int #season_average_ints
                key_int += 1

                self.s_of_t_matrix[2, x] = day.weekday()

                x += 1

    def make_deseasonalised_tables(self):
        #make season averages and also season week data
        #key will hold the index of the first int in the season's range
        self.season_averages = np.zeros((1, self.s_of_t_matrix.shape[1]))
        self.week_averages = np.zeros((1, self.s_of_t_matrix.shape[1]))
        self.day_of_week_averages = np.zeros((1, self.s_of_t_matrix.shape[1]))

        #loop initialization variables
        season_begining = 0
        week_beginning = 0

        comparison = self.s_of_t_matrix[0,0]
        season_total = [comparison]
        week_tot = [comparison]
        day_of_week_collection = {self.s_of_t_matrix[2,0]: [self.s_of_t_matrix[0,0]]}

        for x in range(1, self.s_of_t_matrix.shape[1]):
            #day of week initialization
            if self.s_of_t_matrix[2,x] not in day_of_week_collection.keys():
                day_of_week_collection[self.s_of_t_matrix[2,x]] = []
            #initialize everything
            if x == (self.s_of_t_matrix.shape[1] - 1) or self.s_of_t_matrix[1, (x + 1)] == 0:
                if x == (self.s_of_t_matrix.shape[1] - 1): #this is the last day and we still need to add all the last values
                    s_of_t = self.s_of_t_matrix[0,x]
                    week_tot.append(s_of_t)
                    season_total.append(s_of_t)
                    day_of_week_collection[self.s_of_t_matrix[2,x]].append(s_of_t)

            # a new season cluster has started, make calculation
                #do the day_of_week averages
                day_averages = {}
                for day_int, all_list in day_of_week_collection.iteritems():
                    try:
                        day_averages[day_int] = float(sum(all_list))/len(all_list)
                    except ZeroDivisionError:
                        #because this cluster is less than a consecutive week.
                        #NEED TO DECIDE if we should then match the day_average to the closest day like this one.  or, just average the day averages for the whole season in general
                        looking_for_day = True
                        go_back = 1
                        while (looking_for_day):
                            if self.s_of_t_matrix[2,(x - go_back)] == day_int:
                                last_similar = x - go_back
                                looking_for_day = False
                            elif (x - go_back) > -1:
                                go_back += 1

                        day_averages[day_int] = day_averages[last_similar]

                #season average
                this_season_average = float(sum(season_total))/len(season_total)

                for i in range(season_begining, x + 1):
                    self.season_averages[0,i] = this_season_average
                    self.day_of_week_averages[0,i] = day_averages[ self.s_of_t_matrix[2, i] ]

                #do the week
                week_average = float(sum(week_tot))/len(week_tot)
                for i in range(week_beginning, x + 1):
                    self.week_averages[0, i] = week_average

                week_beginning = x + 1
                week_tot = []

                #reset the important season stuff
                season_begining = x + 1
                season_total = []
                day_of_week_collection = {}


            else: #we are still in this season cluster
                #add to season collection
                s_of_t = self.s_of_t_matrix[0,x]

                season_total.append(s_of_t)
                day_of_week_collection[self.s_of_t_matrix[2,x]].append(s_of_t)

                #check to see if this is a new week
                if (self.s_of_t_matrix[1,x] % 7) == 0: #it is a new week
                    week_average = float(week_tot)/len(week_tot)
                    for i in range(week_beginning, x):
                        self.week_averages[0, i] = week_average

                    week_beginning = x + 1
                    week_tot = []
                else:
                    week_tot.append(s_of_t)

                #update important values

    def de_season(self, this_input, type_of_thing):
        final = []

        for x in range(0, self.s_of_t_matrix.shape[1]):
            if this_input[x] == 0 or type_of_thing[0, x] == 0:
                final.append(0)
            else:
                final.append( float(this_input[x])/type_of_thing[0, x] )
        return final

    '''
    day and point of view are ints.  Day is the int after the last full day of trining that we are predicting for.  Point of view is the  perspective we hav after training
    '''
    def predict_forecasted_s_t(self, day, point_of_view):

        if point_of_view < 0 or day < 0:
            print "you put in values to predict for trend analysis that are within the training period.  Try again"
            return None

        predicted_s_of_t = self.holtwinters_object.estimate(day, point_of_view)

        #think about how to do the day_of_week_averages, which will be messed up
        reseasonalised = predicted_s_of_t * self.season_averages[0, day] * self.week_averages[0, day] * self.day_of_week_averages[0, (day - 1)]

        return reseasonalised


def test_all_10():
    #input: (in day order:) check_in: day: s(t), day: s(t), check-IN..
    test_input = {"today": {datetime.date(2014, 1, 1): 10, datetime.date(2014, 1, 2): 10, datetime.date(2014, 1,3): 10, datetime.date(2014, 1, 4): 10, datetime.date(2014, 1, 5): 10, datetime.date(2014, 1, 6): 10, datetime.date(2014, 1, 7): 10 } }
    #expectation should be that everything is 10

    my_estimator = TrendEstimator(test_input)

    prediction = my_estimator.predict_forecasted_s_t(2, 2)

    #expect prediction to be 10

    print "hello"

def test():
    #test_input = {datetime.date(2014, 1, 1): {datetime.date(2014, 1, 3): 0, datetime.date(2014, 1, 1): 2, datetime.date(2014, 1, 2): 3, datetime.date(2014, 1, 4): 0, datetime.date(2015, 1,5): 1, datetime.date(2014, 1, 6): 4, datetime.date(2014, 1,7): 2}}
    #
    test_input = {datetime.date(2014, 1, 1): {datetime.date(2014, 1, 3): 0, datetime.date(2014, 1, 1): 1, datetime.date(2014, 1, 2): 1, datetime.date(2014, 1, 4): 2, datetime.date(2015, 1,5): 1, datetime.date(2014, 1, 6): 3, datetime.date(2014, 1,7): 2}}

    my_estimator = TrendEstimator(test_input)

    prediction = my_estimator.predict_forecasted_s_t(1, 1)

if __name__ == '__main__':
    #test_all_10()
    test()



