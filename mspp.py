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

def load_data(csvfile):
    closing = []

    with open(csvfile, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            closing.append((row[0],row[-1]))

    return closing

def offering_data(closing_data):
    assert len(closing_data) >= 2
    oct_re = re.compile(r'.+-10-\d\d$')
    apr_re = re.compile(r'.+-04-\d\d$')
    offering = []

    for current,next in zip(closing_data,closing_data[1:]):
        for regex in (oct_re,apr_re):
            if regex.match(current[0]) and not regex.match(next[0]):
                offering.append(current)
                break
        
    offering.reverse()    
    return offering

def exercise_data(closing_data):
    exercise = []
    mar_re = re.compile(r'.+-03-\d\d$')
    sep_re = re.compile(r'.+-09-\d\d$')

    for current,next in zip(closing_data,closing_data[1:]):
        for regex in (mar_re,sep_re):
            if not regex.match(current[0]) and regex.match(next[0]):
                exercise.append(next)
                break
        
    exercise.reverse()
    return exercise

def buy_and_hold(offering,exercise):
    shares = 0
    contribution = 1000
    count = 4
    for off,ex in zip(offering,exercise[1:]):
        
        count -= 1
        
        price = 0.85 * min(float(ex[1]),float(off[1])) * 1.0
        shares += contribution / price
        
        print "%s %s %s %s" % (off[0],off[1],ex[0],ex[1]),
        
        if ex[1] < off[1] or count == 0:
            count = 4
            print "reset"
        else:
            print "no reset"
        
        
    print shares

        
if __name__ == "__main__":
    company = sys.argv[1]
    #write_csv(company)
    closing_data = load_data(company + '.csv')
    offering_prices = offering_data(closing_data)
    exercise_prices = exercise_data(closing_data)
    buy_and_hold(offering_prices,exercise_prices)
