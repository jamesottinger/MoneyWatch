# MoneyWatch <img src="https://api.travis-ci.org/jamesottinger/MoneyWatch.svg?branch=master" alt="Build status" />

### Introduction

MoneyWatch is a web application that was created to help manage my money and investments.
The focus of MoneyWatch is on bank registers (Savings/Checking/Debt) and investment portfolio
and returns tracking (Stocks/Mutual Funds).

### Goals

This is one of my personal projects that I work on in my spare time, usually each month during bill paying time! ;)

The original goal was to track my own money and investments while tackling some of the pain points of my
former money management tool (the late M$ Money 2002). MoneyWatch does some things very well,
and others it just doesn't do at all. With MoneyWatch, you'll gain control of your finances.


### What is it made out of?

MoneyWatch is a mix of HTML5, CSS3, and JavaScript on the front-end. Python3 with Flask drive the back-end with MySQL data storage.
Frameworks used include a mix of jQuery, jQuery UI, YUI 3, and Bootstrap 3. HighCharts is used for the graphing pieces.
MoneyWatch pulls stock quotes from Yahoo's Finance API.

### Installation
* Install using the /installation/moneywatch-db.sql file to start out with an empty database.
* Edit /cgi-bin/moneywatchconfig.py and enter the database connection information and log file locations.
* run $ python3 ./relay
* visit 127.0.0.1:5000

### Screenshots

Check out the [screenshots](https://github.com/jamesottinger/moneywatch/blob/master/screenshots/SCREENSHOTS.md "Screenshots").
