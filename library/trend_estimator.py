from holtwinters import estimator, holtwinters
import datetime
import my_time
import numpy as np
import sys
import math
'''
this is a helper class to make the the trend estimator for the Modified MonteCarlo
this calculates now for the whole trianing period
'''

class TrendEstimator():
    #input: (in day order:) check_in: day: s(t), day: s(t), check-IN...
    def __init__(self, point_of_view, season_day_tracker, t_season_tracker, start, end, s_of_t, s_sum_average, s_sum_i, s_week_average):
        self.start = start
        self.end = end
        self.season_average = None
        self.week_i_average = None
        self.week_average = None


        s_des_t = self.make_s_des_t(point_of_view, season_day_tracker,t_season_tracker, s_of_t, s_sum_average, s_sum_i, s_week_average)


        #make holtwinters, hacked it to have just 3 equal seasons, which after deseasonalisation doesn't exit.  But okay
        self.holtwinters_object = holtwinters.HoltWintersEstimator(s_des_t, 3, len(s_des_t)/3)


    '''
    s_des_t = s_of_t/ s_week_average/ s_week_i_average/ season_average

    '''
    def make_s_des_t(self, point_of_view, season_day_tracker, t_season_tracker,s_of_t, s_sum_average, s_sum_i, s_week_average):
        duration = int((self.end - self.start).days)
        self.season_average = np.zeros((1, duration))
        self.week_i_average = np.zeros((1, duration))
        self.week_average = np.zeros((1, duration))

        s_des_t = []

        t = 0
        for day in my_time._daterange(self.start, self.end):
            day_t = (day - datetime.date(2014, 1, 1)).days
            season = t_season_tracker[0, day_t]

            point_view_date = day - datetime.timedelta(point_of_view)
            point_view_date_t = (point_view_date - datetime.date(2014, 1, 1)).days

            #if after finding the point of view, there isn't enough history, fuck it take the normal date, we aren't predicting for this day anyways and our point of view is the day
            if point_view_date_t <= 0:
                point_view_date_t = (day - datetime.date(2014, 1, 1)).days
                point_view_date = day

            history_start = (point_view_date - datetime.timedelta(365))

            if history_start < datetime.date(2014, 1, 1):
                history_start = datetime.date(2014, 1, 1)
                history_start_t = 0
            else:
                history_start_t = (history_start - datetime.date(2014, 1, 1)).days

            #best match is: get the history_start t,
            weekday_diff = abs(history_start.weekday() - day.weekday())
            match_day = self.find_best_match(day, season_day_tracker[season], history_start, point_view_date)
            match_t = (match_day - datetime.date(2014, 1, 1)).days

            #best matched s_t
            this_s_t = s_of_t[0, match_t]

            #take out season average

            sorted_season = sorted([entry for entry in season_day_tracker[season] if entry >= history_start_t and entry <= point_view_date_t])

            #sometimes there is not enought data for this
            if not sorted_season:
                continue

            season_length = len(sorted_season)

            season_end_t = sorted_season[season_length - 1]
            season_start_t = sorted_season[0]

            #always make sure 0 is centered at 1
            season_sum = (s_sum_average[0, season_end_t] - s_sum_average[0, season_start_t]) + 1
            season_average = float(season_sum)/season_length

            #update values
            self.season_average[0, t] = season_average

            s_des_1_1 = this_s_t/season_average

            #take out the week-average
            self.week_average[0,t] = s_week_average[0, match_t]
            s_prime_t = s_des_1_1/s_week_average[0, match_t]

            #take out day_week_average, always make sure 0 is centered at 1
            sum_i = (s_sum_i[season][day.weekday()][0, season_end_t] - s_sum_i[season][day.weekday()][0, season_start_t]) + 1


            i_count = (s_sum_i[season][day.weekday()][1, point_view_date_t] - s_sum_i[season][day.weekday()][1, history_start_t])

            if i_count == 0:
                #hack this real quick, sometimes when we predict a bit too far int he future, there hasn't been a day in the predicted date's season.  But there shouldn't be a sum_i either.  So we will just call it 0, or in this case 1 because of the centering

                i_count = 1
                sum_i = 1

            i_average = float(sum_i)/i_count

            self.week_i_average[0, t] = i_average
            this_s_des_t = s_prime_t/i_average

            s_des_t.append(this_s_des_t)

            t += 1

            #TEST
            if math.isnan(this_s_des_t):
                print "hello, this_s_des_t is 0"
                sys.exit()

        return s_des_t

    def find_best_match(self, day, season_day_tracker_this_season, history_start, point_view_date):
        search_weekday = day.weekday()

        #must have at least one nth weekday
        nth_weekday = ((day - point_view_date).days / 7) + 1

        i_counter = []
        for test_t in season_day_tracker_this_season:
            test_day = datetime.date(2014, 1, 1) + datetime.timedelta(test_t)
            if test_day.weekday() == search_weekday:
                i_counter.append(test_day)
            if len(i_counter) == nth_weekday:
                return test_day

        #if we never find an appropriate day, then we are going to return the last day that matches.  This should not happen with the limited test range
        return i_counter[-1]

    '''
    can take date time object
    '''
    def predict_forecasted_s_t(self, day):
        if not isinstance(day, int):
            this_t = (day - datetime.date(2014, 1, 1)).days
        else:
            this_t = day

        predicted_s_of_t = self.holtwinters_object.estimate(this_t + 1, this_t)

        season_average = self.season_average[0, this_t]
        day_week = self.week_i_average[0, this_t]
        week_average = self.week_average[0, this_t]

        #think about how to do the day_of_week_averages, which will be messed up
        #
        reseasonalised = predicted_s_of_t * season_average * day_week *week_average

        return reseasonalised


def test_all_10():
    #input: (in day order:) check_in: day: s(t), day: s(t), check-IN..
    test_input = {"today": {datetime.date(2014, 1, 1): 10, datetime.date(2014, 1, 2): 10, datetime.date(2014, 1,3): 10, datetime.date(2014, 1, 4): 10, datetime.date(2014, 1, 5): 10, datetime.date(2014, 1, 6): 10, datetime.date(2014, 1, 7): 10 } }
    #expectation should be that everything is 10

    my_estimator = TrendEstimator(test_input)

    prediction = my_estimator.predict_forecasted_s_t(2, 2)

    #expect prediction to be 10

def test():
    import MonteCarlo_new
    import json
    import time

    with open('../data/sample.json') as jsonFile:
        reservation_dict = json.load(jsonFile)

    monte_defined_base = time.time()

    monte_defined = MonteCarlo_new.ModifiedMonteCarlo(datetime.date(2015, 3, 1), datetime.date(2015, 3, 30), reservation_dict, 0)

    monte_cost = time.time() - monte_defined_base

    prediction = monte_defined.trend.predict_forecasted_s_t(datetime.date(2015, 1, 10))

    #expect 1
    print prediction

if __name__ == '__main__':
    #test_all_10()
    test()



