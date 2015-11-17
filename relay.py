#!/ usr/bin/env python3
#===============================================================================
# Copyright (c) 2015, James Ottinger. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# MoneyWatch - https://github.com/jamesottinger/moneywatch
#===============================================================================
from flask import Flask
import sys
sys.path.append('/dirsomewhere/')
import moneywatchengine

app = Flask(__name__)
#===============================================================================
