/*
#===============================================================================
# Copyright (c) 2016, James Ottinger. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# MoneyWatch - https://github.com/jamesottinger/moneywatch
#===============================================================================

Creates an empty MySQL database for MoneyWatch.

*/

CREATE TABLE `moneywatch_bankaccounts` (
  `bacctid` int(11) NOT NULL AUTO_INCREMENT,
  `bacctname` varchar(255) DEFAULT NULL,
  `mine` tinyint(4) DEFAULT '0',
  `accountnumber` varchar(30) DEFAULT '',
  `accounttype` varchar(50) DEFAULT NULL,
  `bank` varchar(255) DEFAULT NULL,
  `totalall` decimal(14,2) DEFAULT NULL,
  `totaluptotoday` decimal(14,2) DEFAULT NULL,
  `todaywas` date DEFAULT NULL,
  `tallytime` datetime DEFAULT NULL,
  PRIMARY KEY (`bacctid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `moneywatch_bankbills` (
  `payeeid` int(11) NOT NULL AUTO_INCREMENT,
  `payeename` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`payeeid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `moneywatch_banktransactions` (
  `btransid` int(11) NOT NULL AUTO_INCREMENT,
  `bacctid` int(11) NOT NULL,
  `transdate` date NOT NULL,
  `type` varchar(4) NOT NULL,
  `updown` varchar(4) DEFAULT NULL,
  `amt` decimal(14,2) NOT NULL,
  `whom1` varchar(255) DEFAULT NULL,
  `whom2` varchar(255) DEFAULT NULL,
  `numnote` varchar(50) DEFAULT NULL,
  `reconciled` tinyint(4) DEFAULT '0',
  `splityn` tinyint(4) DEFAULT '0',
  `transferbtransid` int(11) DEFAULT '0',
  `transferbacctid` int(11) DEFAULT '0',
  `itransid` int(11) DEFAULT '0',
  PRIMARY KEY (`btransid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `moneywatch_banktransactions_splits` (
  `bacctid` int(11) NOT NULL,
  `btransid` int(11) NOT NULL,
  `whom1` varchar(255) DEFAULT NULL,
  `whom2` varchar(255) DEFAULT NULL,
  `amt` decimal(14,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `moneywatch_invelections` (
  `ielectionid` int(11) NOT NULL AUTO_INCREMENT,
  `iacctname` varchar(255) DEFAULT NULL,
  `ielectionname` varchar(255) DEFAULT NULL,
  `ticker` varchar(20) DEFAULT NULL,
  `divschedule` varchar(20) DEFAULT NULL,
  `shares` decimal(10,3) DEFAULT NULL,
  `sharesareunits` tinyint(4) DEFAULT '0',
  `sweep` tinyint(4) DEFAULT '0',
  `active` tinyint(4) DEFAULT NULL,
  `fetchquotes` tinyint(4) DEFAULT NULL,
  `sharesbydividend` decimal(10,3) DEFAULT '0',
  `sharesfromemployer` decimal(10,3) DEFAULT '0',
  `costbasis` decimal(14,2) DEFAULT NULL,
  `costbasisbydividend` decimal(14,2) DEFAULT '0',
  `costbasisfromemployer` decimal(14,2) DEFAULT '0',
  `costbasisme` decimal(14,2) DEFAULT '0',
  `balance` decimal(14,2) DEFAULT NULL,
  `manualoverrideprice` decimal(14,2) DEFAULT NULL,
  `quotedate` datetime DEFAULT NULL,
  `quoteprice` decimal(14,2) DEFAULT NULL,
  `lastcloseprice` decimal(14,2) DEFAULT NULL,
  `yield` varchar(100) DEFAULT NULL,
  `quotechange` varchar(100) DEFAULT NULL,
  `divdatenext` varchar(100) DEFAULT NULL,
  `divdateprev` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`ielectionid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `moneywatch_invtransactions` (
  `itransid` int(11) NOT NULL AUTO_INCREMENT,
  `ielectionid` int(11) DEFAULT '0',
  `btransid` int(11) DEFAULT '0',
  `transdate` date DEFAULT NULL,
  `ticker` varchar(20) DEFAULT NULL,
  `updown` varchar(20) DEFAULT NULL,
  `action` varchar(20) DEFAULT NULL,
  `sharesamt` decimal(10,3) DEFAULT '0',
  `shareprice` decimal(14,2) DEFAULT '0',
  `transprice` decimal(14,2) DEFAULT '0',
  `totalshould` decimal(14,2) DEFAULT '0',
  PRIMARY KEY (`itransid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
