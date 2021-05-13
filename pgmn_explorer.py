from __future__ import print_function
import pandas as pd
import streamlit as st
import altair as alt
from datetime import date

import tools

current_year = date.today().year
first_year = 2001

class App:
    def __init__(self, df_stations, df_waterlevels, df_precipitation, df_wl_stations, df_precipitation_stations):
        self.df_stations = df_stations
        self.df_waterlevels = df_waterlevels
        self.df_precipitation = df_precipitation
        self.df_wl_stations = df_wl_stations
        self.df_precipitation_stations = df_precipitation_stations

        self.settings = {}
        self.lst_conservation_authorities = list(df_stations['CONS_AUTHO'].unique())
        self.lst_aquifer = list(df_stations['AQUIFER_TY'].unique())
        self.stations = []
    
    def show_menu(self):

        def get_stations():
            df =  self.df_stations
            if len(self.settings['cons_authorities']) > 0:
                filter = df['CONS_AUTHO'].isin(self.settings['cons_authorities']) 
                df =  self.df_stations[filter]
            
            if len(self.settings['aquifer_types']) > 0:
                filter = df['AQUIFER_TY'].isin(self.settings['aquifer_types'])
                df =  df[filter]

            return list(df['PGMN_WELL'])

        def show_plot():            
            config={}
            config['width'] =  self.settings['width']
            config['height'] = self.settings['height']
            config['year_from'] = self.settings['year_from']
            config['year_to'] = self.settings['year_to']
            config['rolling_avg_int'] = 0 # todo: self.settings['rolling_avg_int']
            for station in self.settings['stations']:
                config['title'] = f"{station} ({self.settings['year_from']} - {self.settings['year_to']})"
                df_wl = self.df_waterlevels[self.df_waterlevels['CASING_ID'] == station] 
                location_id = int(df_wl.iloc[0]['location_id'])
                df_prec = self.df_precipitation[self.df_precipitation['location_id'] == location_id] 
                
                if self.settings['group_by_year']:
                    for year in range(self.settings['year_from'], self.settings['year_to']):  
                        config['year_from'] = year
                        config['year_to'] = year

                        config['title'] = f"{station} ({year})"                      
                        if len(df_wl[(df_wl['year'] == year)]) > 0: 
                            config['title'] = f'{station} ({year})'

                            fig = self.plot_time_series(df_wl, df_prec, config)
                            st.write(fig) 
                elif len(df_wl) > 50:
                    df_wl = df_wl[ (df_wl['year']>= self.settings['year_from']) & (df_wl['year']<= self.settings['year_to']) ]
                    config['title'] = f"{station} ({self.settings['year_from']} - {self.settings['year_to']})"
                    config['width'] =  self.settings['width']
                    config['height'] = self.settings['height']
                    config['rolling_avg_int'] = 0 # todo: self.settings['rolling_avg_int']
                    fig = self.plot_time_series(df_wl, df_prec, config)
                    st.write(fig)

        def show_filter():
            default=[self.lst_conservation_authorities[0]]
            self.settings['cons_authorities'] = st.sidebar.multiselect("🔎 Conservation authority", self.lst_conservation_authorities, [])
            default=[self.lst_aquifer[0]]
            self.settings['aquifer_types'] = st.sidebar.multiselect("🔎 Aquifer types", self.lst_aquifer, [])
            lst_stations = get_stations()
            default = [lst_stations[0]]
            self.settings['stations'] = st.sidebar.multiselect("🎯 Station", lst_stations, default)
            self.settings['year_from'], self.settings['year_to'] = st.sidebar.select_slider("Years", range(first_year,current_year),[current_year-6,current_year-1])
            self.settings['group_by_year'] = st.sidebar.checkbox("Group plots by year")
            self.settings['width'] = st.sidebar.number_input('Plot width (px)', value=800,min_value=100,max_value=10000)
            self.settings['height']= st.sidebar.number_input('Plot height (px)', value=300,min_value=100,max_value=10000)
            #self.settings['use_common_y']= st.sidebar.checkbox('Use common min/max Y-values for each plot')
            #self.settings['max_y']= st.sidebar.number_input('Maximum y')
            self.settings['rolling_avg_int']= 0 #todo: st.sidebar.number_input('Rolling average interval', value=0,min_value=0,max_value=100000)
        
        show_filter()
        show_plot()

    def plot_time_series(self, df_wl, df_prec, config):
        min_year = config['year_from']
        max_year = config['year_to'] + 1
        filter = df_wl['wl_elev'].notna() # make sure there are no Null values 
        min_y= df_wl[filter]['wl_elev'].min()
        max_y= df_wl['wl_elev'].max()
        min_y= tools.truncate(min_y, 0) 
        
        max_y= tools.truncate(max_y + 1, 0) 

        waterlevels = alt.Chart(df_wl).mark_line(clip=True).encode(
            alt.X('date:T',
                scale = alt.Scale(domain=(f'01-01-{min_year}', f'01-01-{max_year}')),
                axis=alt.Axis(title=""),
            ),
            alt.Y('wl_elev:Q', 
                scale = alt.Scale(domain=(min_y,max_y)),
                axis=alt.Axis(title="water level (masl)"),
            ),
            tooltip=['CASING_ID', 'date', 'wl_elev']
        )
        if config['rolling_avg_int'] > 0:
            rolling_avg = alt.Chart(df_wl).mark_line(
                    color='red',
                    size=2
                ).transform_window(
                    rolling_mean='mean(wl_elev)',
                    frame=[-config['rolling_avg_int'] / 2, config['rolling_avg_int'] / 2],
            ).encode(
                x='date:T',
                y='rolling_mean:Q'
            )
        if len(df_prec) > 0:
            precipitation = alt.Chart(df_prec).mark_bar(color='grey', size=1, clip=True).encode(
            alt.X('date:T',
                scale = alt.Scale(domain=(f'01-01-{min_year}', f'01-01-{max_year}')),
                axis=alt.Axis(title=""),
                
            ),
            alt.Y('AccumulationFinal:Q', 
                sort='descending',
                scale = alt.Scale(domain=[0,100]),                
                axis=alt.Axis(title="precipitation(mm)"),
            ),
            tooltip=['date', 'AccumulationFinal']
        )


        if config['rolling_avg_int'] > 0:
            fig = (waterlevels + rolling_avg)
        elif len(df_prec) > 0:
            fig = alt.layer(waterlevels, precipitation).resolve_scale(y='independent')
        else:
            fig = waterlevels

        fig = fig.properties(
            title=config['title'],
            width=config['width'],
            height=config['height']
        )
        return fig
    

