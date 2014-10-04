# MoneyWatch

### Introduction

MoneyWatch is a web application that was created to help manage my money. The focus of MoneyWatch is on bank registers
(Savings/Checking/Debt) and investment (Stocks/Mutual Funds) portfolio and returns tracking.

### Goals

This is one of my personal projects that I work on in my spare time, usually each month during bill paying time! ;)

The original goal was to track my own money and investments while tackling some of the pain points of my
former money management tool (M$ Money 2002).  MoneyWatch does some things very well, and others just it doesn't do at all.

### What is it made out of?

MoneyWatch is a mix of HTML5, CSS3, and JavaScript on the front-end and Python on the back-end with MYSQL data storage.
Frameworks used include a mix of jQuery, jQuery UI, YUI 3, and HighCharts for graphing.

### Installation
You'll need MYSQL and a computer. :)
* Install using the /installation/moneywatch.sql file to start out with an empty database.
* Adjust the g_dbauth creds (line 13 in /cgi-bin/moneywatchengine.py) to get it wired up.
* Point your webserver at it and visit moneywatch.html
