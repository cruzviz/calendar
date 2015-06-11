# -*- coding: utf-8 -*-
from tides import Tides
from astro import Astro
from cal_draw import generate_annual_calendar
import argparse
import os
#import pickle

parser = argparse.ArgumentParser()
parser.add_argument('filename',
                    help = 'Path to a NOAA annual tide prediction file.')
args = parser.parse_args()

if not os.path.isfile(args.filename):
    raise IOError('Cannot find ' + args.filename)
print('Making Sun * Moon * Tides Calendar with ' +
        'input file ' + args.filename)

tides = Tides(args.filename)
print(tides.station_name + ', ' + tides.state)
sun = Astro(tides.latitude, tides.longitude, tides.timezone, tides.year, 'Sun')
print('Sun calculations complete')
moon = Astro(tides.latitude, tides.longitude, tides.timezone, tides.year, 'Moon')
print('Moon calculations complete')

# save sun, moon, tides in pickle or json in a new folder
# ?? make new folder ??
#with open('sun_moon_tide_data.pickle', 'wb') as f:
#    pickle.dump([sun, moon, tides], f, pickle.HIGHEST_PROTOCOL)
#print('Computations complete, pickled in @@@wherever.')

print('Starting to draw calendar now.')
generate_annual_calendar(tides, sun, moon, 'testcal')
# @@@@@@@
#
#
print('Calendar complete. Find output testcal.pdf @@@@')