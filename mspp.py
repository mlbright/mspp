#!/usr/bin/python

import csv
import re
import urllib
import sys

def adjust_month(month):
    if month > 12 or month < 1:
        raise Exception("Invalid month")
    month -= 1 # Month for yahoo is 0 based
    return month

def get_last_day(month):
    ret = 31
    if month in (4, 6, 9, 11):
        ret = 30
    elif month == 2:
        ret = 28
    return ret

def download_instrument_prices(instrument, fromMonth, fromYear, toMonth, toYear):
    fromDay = 1
    toDay = get_last_day(toMonth)
    fromMonth = adjust_month(fromMonth)
    toMonth = adjust_month(toMonth)
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

def load_closing_data(csvfile):
    tmp = []

    with open(csvfile, 'rb') as f:
        reader = csv.reader(f)
        tmp = [ (row[0],row[-1]) for row in reader ]
    
    tmp = [ (date_,float(price)) for date_,price in tmp[1:] ]
    assert len(tmp) >= 2
    return tmp
    
def offering(closing_data):
    
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

def exercise(closing_data):
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

def lookback(eperiods):
    lookback_ =  []
    reset = 0
    offering_price = eperiods[0][1]
    purchase_price = None
    for period in eperiods:
        
        if reset == 0:
            #print "price reset!",
            reset = 4
            offering_price = period[1]
            
           
        purchase_price = min(offering_price,period[3])
        lookback_.append((period[2],purchase_price))
        
        #print period,purchase_price
        
        if period[3] < offering_price:
            reset = 0
        else:
            reset -= 1

        
    return lookback_
        
def exercise_periods(offering,exercise,offering_date=None):
    tmp = []
    if offering_date:
        include = False
        for off,ex in zip(offering,exercise[1:]):
            
            if off[0] == offering_date:
                include = True
            if include:
                tmp.append((off[0],off[1],ex[0],ex[1]))
    else:
        tmp = [(off[0],off[1],ex[0],ex[1]) for off,ex in zip(offering,exercise[1:])]
    
    #for rec in tmp:
    #   print rec
        
    return tmp
        
def buy_and_hold(lookback_,contribution):
    shares = 0
    
    for ex_date_,price in lookback_:
                
        price = 0.85 * price
        shares += contribution / price

        
    return shares

def buy_and_sell(lookback_,contribution):

    profit = 0
    for exercise_date_,price in lookback_:
        """
        buy_price = 0.85 * price
        shares = contribution / buy_price
        profit += shares * price
        """
        profit += contribution / 0.85
        
    return profit


    
def print_offering_dates(offering):
    for date_,price in offering:
        print date_

        
if __name__ == "__main__":
    company = sys.argv[1]
    #write_csv(company)
    closing = load_closing_data(company + '.csv')
    #print_offering_dates(offering(closing))
    #epds = exercise_periods(offering(closing),exercise(closing),'2010-04-01')
    epds = exercise_periods(offering(closing),exercise(closing))
    
    
    period_contribution = 120 * 2 * 6
    lookback_ = lookback(epds)
    
    shares = buy_and_hold(lookback_,period_contribution)
    print "buy and hold current value (#shares %.2f * price %.2f): %.2f" % (shares,closing[0][1],shares * closing[0][1])
    
    print "buy and sell profit: %.2f" % (buy_and_sell(lookback_,period_contribution))