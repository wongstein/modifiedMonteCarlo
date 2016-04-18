import datetime

'''
takes datetime for start_date and end date
inclues the end dates
'''
def _daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days) ):
        yield start_date + datetime.timedelta(n)


'''
makes a dictionary where the day is the key, and the value is the int which represents the day number away that day is from the start date
inputs: datetime object for both start_date and end_date, ideally,
'''
def day_int_dict(start_date, end_date):
    final_dict = {}
    try:
        time_difference = (end_date-start_date).days
    except Exception as e:
        time_difference = (datetime.strptime(end_date, "%Y-%m-%d").date() - datetime.strptime(start_date, "%Y-%m-%d").date() ).days

    for n in range(0, int (time_difference) + 1): #weird bug, missing the last day, this is a hack
        final_dict[(start_date + datetime.timedelta(n)).strftime("%Y-%m-%d")] = n

    return final_dict
'''
makes default structure used in all data dicts, 2008 - 2017
'''
def default_date_structure(years = ["2013", "2014", "2015", "2016"]):
    final = {}
    for year in years:
        final[year] = {}

        for day in _daterange(datetime.date(int(year), 01, 01), datetime.date(int(year), 12, 31)):
            final[year][day.strftime("%Y-%m-%d")] = None

    return final

'''
must be datetime objects as inputs
output: day (datetime):
'''
def compact_default_date_structure(start_date, end_date):
    final = {}
    for day in _daterange(start_date, end_date):
        if day not in final.keys():
            final[day] = {}
        final[day] = None
    return final

'''
input: {active: , deleted_at: , updated_at: , Created_at:}
returns the number of days this listing has been active
returns false if the listing is still active
'''
def get_listing_activity_span(listing_important_dates):

    #listed as not active
    if listing_important_dates["active"] == 0:
                            #deleted
        if listing_important_dates["deleted_at"]:
            return int( (listing_important_dates["deleted_at"] - listing_important_dates["created_at"]).days)
        else:
            return int( (listing_important_dates["updated_at"] - listing_important_dates["created_at"]).days)

    else: #listed as active
        if listing_important_dates["deleted_at"]:
            return int( (listing_important_dates["deleted_at"] - listing_important_dates["created_at"]).days)
        else:
            return False





