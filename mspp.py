#!/usr/bin/python

import csv
import re
import urllib
import sys

def __adjust_month(month):
    if month > 12 or month < 1:
        raise Exception("Invalid month")
    month -= 1 # Month for yahoo is 0 based
    return month

def __get_last_day(month):
    ret = 31
    if month in (4, 6, 9, 11):
        ret = 30
    elif month == 2:
        ret = 28
    return ret

def download_instrument_prices(instrument, fromMonth, fromYear, toMonth, toYear):
    fromDay = 1
    toDay = __get_last_day(toMonth)
    fromMonth = __adjust_month(fromMonth)
    toMonth = __adjust_month(toMonth)
    url = "http://ichart.finance.yahoo.com/table.csv?s=%s&a=%d&b=%d&c=%d&d=%d&e=%d&f=%d&g=d&ignore=.csv"
    url = url % (instrument, fromMonth, fromDay, fromYear, toMonth, toDay, toYear)

    f = urllib.urlopen(url)
    if f.headers['Content-Type'] != 'text/csv':
        raise Exception("Failed to download data")
    buff = f.read()

    # Remove the BOM
    while not buff[0].isalnum():
        buff = buff[1:]

    return buff

def get_daily_csv(instrument, from_year, to_year):
    fromMonth = 1
    toMonth = 12
    return download_instrument_prices(instrument, fromMonth, from_year, toMonth, to_year)

def write_csv(instrument):
    with open(instrument + '.csv','w') as f:
        f.write(get_daily_csv(instrument,2000,2012))

def load_exercise_data(csvfile):
    closing_prices = []
    exercise_data = []
    oct_re = re.compile(r'.+-10-\d\d$')
    apr_re = re.compile(r'.+-04-\d\d$')

    with open(csvfile, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            closing_prices.append((row[0],row[-1]))
    
    assert len(closing_prices) >= 2
    for current,next in zip(closing_prices,closing_prices[1:]):
        for regex in (oct_re,apr_re):
            if regex.match(current[0]) and not regex.match(next[0]):
                exercise_data.append(current)
                break
        
    exercise_data.reverse()    
    return exercise_data

def buy_and_hold(exercise_data):
    pass 
        
if __name__ == "__main__":
    company = sys.argv[1]
    write_csv(company)
    print load_exercise_data(company + '.csv')
