# -*- coding: utf-8 -*-
"""
Module for drawing a Sun * Moon * Tide calendar using matplotlib. Main
function is generate_annual_calendar. Various helper functions may also be
useful in other applications.
"""
import matplotlib
matplotlib.use('PDF')
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
plt.ioff()
from matplotlib.backends.backend_pdf import PdfPages

import calendar
import numpy as np
import pandas as pd
from PIL import Image
import pkgutil
from io import BytesIO


def days_in_month(year_month_string):
    '''Generator that takes year_month_string (i.e. '2015-07') and yields
    all the days of the month in order, also as strings (i.e. '2015-07-18').
    '''
    start_date = pd.to_datetime(year_month_string)
    _, days_in_month = calendar.monthrange(start_date.year, start_date.month)
    end_date = start_date + pd.DateOffset(days_in_month)
    current_date = start_date
    while current_date < end_date:
        yield current_date.strftime('%Y-%m-%d')
        current_date = current_date + pd.DateOffset()


def months_in_year(year_string):
    '''Generator that takes year_string (i.e. '2015') and yields all the months
    of the year in order, also as strings (i.e. '2015-07').
    '''
    start_date = pd.to_datetime(year_string + '-01')    
    end_date = start_date + pd.DateOffset(months=12)
    current_date = start_date
    while current_date < end_date:
        yield current_date.strftime('%Y-%m')
        current_date = current_date + pd.DateOffset(months=1)


def generate_annual_calendar(tide_obj, sun_obj, moon_obj, file_name):
    '''Take tide, sun, and moon objects and generate a PDF file named
    `file_name`, which is a complete annual Sun * Moon * Tide calendar. File is
    saved to current working directory. Verbose output since this is a slow
    function.
    
    Args:
    tide_obj: tides.Tides object
    sun_obj: astro.Astro object for 'Sun'
    moon_obj: astro.Astro object for 'Moon'
    file_name: string. ".pdf" will NOT be appended to the file_name so the .pdf
                extension ought to be included in file_name.
    '''
    with PdfPages(file_name) as pdf_out:
        #@@ first make cover
        #@@ then make About page
        #@@ then make Year-at-a-Glance

        for month in months_in_year(tide_obj.year):
            monthfig = month_page(month, tide_obj, sun_obj, moon_obj)
            print(month + " figure created, now saving...")
            monthfig.savefig(pdf_out, format='pdf')
            print("Saved " + month)
        
        #@@ add page for Technical Details        
        
        d = pdf_out.infodict()
        d['Title'] = 'Sun * Moon * Tide ' + tide_obj.year + ' Calendar'
        d['Author'] = 'Sara Hendrix, CruzViz'
        d['Subject'] = tide_obj.station_name + ", " + tide_obj.state
        d['CreationDate'] = pd.Timestamp.now().to_pydatetime()    
    
    
    
def month_page(month_string, tide_o, sun_o, moon_o):
    '''Builds an 8.5x11" matplotlib Figure for a month page of the
    Sun * Moon * Tide calendar.
    
    Arguments:
        month_string: string of the month to be drawn, i.e. '2015-07'
        tide_o: tides.Tides object
        sun_o: astro.Astro object for 'Sun'
        moon_o: astro.Astro object for 'Moon'
    
    Returns:
        fig: matplotlib.pyplot Figure object, ready for writing to PDF.
    '''
    fig = plt.figure(figsize=(8.5,11))
    
    tide_min, tide_max = tide_o.annual_min, tide_o.annual_max
    place_name = tide_o.station_name + ", " + tide_o.state
    time_zone = tide_o.timezone
    month_title = pd.to_datetime(month_string).strftime('%B')
    year_title = tide_o.year
    
    def _plot_a_date(grid_index, date):
        '''Internal function. Works on pre-defined gridspec gs and assumes
        variables like tide_min, tide_max, month_of_tide/moon/sun already
        defined in outer scope.
        
        Plots the two daily subplots for `date` in gridspec coordinates
        gs[grid_index] for the sun/moon and gs[grid_index + 7] for tide.
        `date` must be a string in %Y-%m-%d format, i.e. '2015-07-18'.
        
        Returns ax1, ax2 = sun/moon (ax1) and tide (ax2) subplot handles
        '''
        day_of_sun = sun_o.heights[date]
        day_of_moon = moon_o.heights[date]
        day_of_tide = tide_o.all_tides[date]
        
        # convert indices to matplotlib-friendly datetime format
        Si = day_of_sun.index.to_pydatetime()
        Mi = day_of_moon.index.to_pydatetime()
        Ti = day_of_tide.index.to_pydatetime()
        
        # zeros for plotting the filled area under each curve
        Sz = np.zeros(len(Si))
        Mz = np.zeros(len(Mi))
        Tz = np.zeros(len(Ti))
        
        # x-limits from midnight to 11:59pm local time
        start_time = pd.to_datetime(date + ' 00:00').tz_localize(time_zone)
        start_time = matplotlib.dates.date2num(start_time.to_pydatetime())
        stop_time = pd.to_datetime(date + ' 23:59').tz_localize(time_zone)
        stop_time = matplotlib.dates.date2num(stop_time.to_pydatetime())
        
        # sun and moon heights on top
        ax1 = plt.subplot(gs[grid_index])
        ax1.fill_between(Si, day_of_sun, Sz, color='#FFEB00', alpha=1)
        ax1.fill_between(Mi, day_of_moon, Mz, color='#D7A8A8', alpha=0.2)
        ax1.set_xlim((start_time, stop_time))
        ax1.set_ylim((0, 1))
        ax1.set_xticks([])
        ax1.set_yticks([])
        for axis in ['top','left','right']:
            ax1.spines[axis].set_linewidth(1.5)
        ax1.spines['bottom'].set_visible(False)
        # add date number
        plt.text(0.05, 0.73, day_of_sun.index[0].day, ha = 'left',
                 fontsize = 12, fontname='Foglihten',
                 transform = ax1.transAxes)
        # add moon phase icon
        moon_icon = '0ABCDEFGHIJKLM@NOPQRSTUVWXYZ'
        plt.text(0.96, 0.69, moon_icon[moon_o.phase_day_num[date]],
                 ha = 'right', fontsize = 12, fontname='moon phases',
                 transform = ax1.transAxes)
        
        # tide magnitudes below
        ax2 = plt.subplot(gs[grid_index + 7])
        ax2.fill_between(Ti, day_of_tide, Tz, color='#52ABB7', alpha=0.8)
        ax2.set_xlim((start_time, stop_time))
        ax2.set_ylim((tide_min, tide_max))
        ax2.set_xticks([])
        ax2.set_yticks([])
        for axis in ['bottom','left','right']:
            ax2.spines[axis].set_linewidth(1.5)
        ax2.spines['top'].set_linewidth(0.5)
        
        return ax1, ax2
    
# ---------------- build grid of daily plots ---------------------
    gs = gridspec.GridSpec(12, 7, wspace = 0.0, hspace = 0.0)
    daily_axes = [] # daily_axes[i] will hold sun/moon axes for date i+1

    # dayofweek = The day of the week with Monday=0, Sunday=6    
    init_day = (pd.to_datetime(month_string + '-01').dayofweek + 1) % 7
    gridnum = init_day
    for day in days_in_month(month_string):
        ax, _ = _plot_a_date(gridnum, day)
        daily_axes.append(ax)
        if pd.to_datetime(day).dayofweek == 5: # if just plotted a Saturday
            gridnum += 8  # skip down a week to leave tide subplots intact
        else:
            gridnum += 1

    fig.subplots_adjust(left=0.05, right=0.95,
                        bottom=0.1, top=0.8,
                        hspace=0.0, wspace=0.0)

    # add solstice or equinox icon, if needed this month
        # @@@@@@@@

    # add empty date boxes, figure annotations and titles
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                 'Friday', 'Saturday']
    for i in range(init_day, 7):
        plt.text(0.5, 1.08, day_names[i],
                 horizontalalignment='center',
                 fontsize=12, fontname='Foglihten',
                 transform = daily_axes[i - init_day].transAxes)
    for i in range(init_day):  # blank boxes on top row
        temp_ax = plt.subplot(gs[i])
        temp2_ax = plt.subplot(gs[i + 7])
        temp_ax.set_xticks([])
        temp_ax.set_yticks([])
        temp2_ax.set_xticks([])
        temp2_ax.set_yticks([])
        for axis in ['left','right']:
            temp_ax.spines[axis].set_linewidth(0.5)
            temp2_ax.spines[axis].set_linewidth(0.5)
        if i == 0:
            temp_ax.spines['left'].set_linewidth(1.5)
            temp2_ax.spines['left'].set_linewidth(1.5)
        if i == (init_day - 1):
            temp_ax.spines['right'].set_linewidth(1.5)
            temp2_ax.spines['right'].set_linewidth(1.5)
        temp_ax.spines['bottom'].set_linewidth(0.0)
        temp2_ax.spines['top'].set_linewidth(0.0)
        temp_ax.spines['top'].set_linewidth(1.5)
        temp2_ax.spines['bottom'].set_linewidth(1.5)
        plt.text(0.5, 1.08, day_names[i],
                     horizontalalignment='center',
                     fontsize=12, fontname='Foglihten',
                     transform = temp_ax.transAxes)

    fig.text(0.05, 0.875, month_title, horizontalalignment='left',
             fontsize='72', fontname='Foglihten')
    fig.text(0.92, 0.875, year_title, horizontalalignment='right',
             fontsize='72', fontname='Foglihten')
    fig.text(0.92, 0.1, place_name, horizontalalignment='right',
             fontsize='16', fontname='Foglihten')
    fig.text(0.92, 0.13, 'Sun * Moon * Tide', horizontalalignment='right',
             fontsize='36', fontname='FoglihtenNo01')
    try:
        logo = pkgutil.get_data('cal_draw', 'graphics/logo.png')
        im = Image.open(BytesIO(logo))
        im = np.array(im).astype(np.float) / 255
        fig.figimage(im, xo = 505, yo = 70)
    except Exception as e:
        print('Could not load logo image. Error: ' + e)  
    
    return fig
    

''' @@@@@@ FUNCTIONS FOR FRONT AND BACK MATTER GENERATION @@@@@@'''



