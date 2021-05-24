from __future__ import print_function
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from datetime import date

import tools
import const as cn

current_year = date.today().year
first_year = 2001
dic_plottypes = {'barchart': 'Barchart', 'heatmap': 'Heatmap'}
time_aggregation = {'barchart': ['day','week','month','year'], 'heatmap': ['week','month']}
class App:
    def __init__(self, df_stations, df_waterlevels, df_precipitation, df_wl_stations, df_precipitation_stations):
        self.df_stations = df_precipitation_stations
        self.df_precipitation = df_precipitation
        self.df_wl_stations = df_wl_stations

        self.settings = {}
        self.lst_conservation_authorities = list(df_stations['CONS_AUTHO'].unique())
        self.lst_conservation_authorities.sort()
        self.lst_aquifer = list(df_stations['AQUIFER_TY'].unique())
        self.stations = []
    

    def plot_barchart(self, df):
        filter = df[self.settings['y']].notna() # make sure there are no Null values         
        min_y= df[filter][self.settings['y']].min()
        max_y= df[self.settings['y']].max()
        min_y= tools.truncate(min_y, 0) 
        max_y= tools.truncate(max_y + 1, 0) 

        fig = alt.Chart(df).mark_bar(size=self.settings['size']).encode(
            alt.X(f"{self.settings['x']}{self.settings['x_data_type']}",
                sort=list(cn.MONTH_DICT),
                axis=alt.Axis(title="", labelAngle=45),
                
            ),
            alt.Y(f"{self.settings['y']}", 
                scale = alt.Scale(domain=[min_y,max_y]),                
                axis=alt.Axis(title="precipitation(mm)"),
            ),
            tooltip=[self.settings['x'], self.settings['y']]
        )

        return fig.properties(width=self.settings['width'], height = self.settings['height'], title = self.settings['title'])
    
    def plot_heatmap(self, df):
        filter = df[self.settings['y']].notna() # make sure there are no Null values         
        min_y= df[filter][self.settings['y']].min()
        max_y= df[self.settings['y']].max()
        min_y= tools.truncate(min_y, 0) 
        max_y= tools.truncate(max_y + 1, 0) 
        fig = alt.Chart(df).mark_rect().encode(
            x=alt.X(f"{self.settings['x']}:O",
                sort=list(cn.MONTH_DICT),
                axis=alt.Axis(labelAngle=45, 
                title=self.settings['x']), 
            ),
            y=alt.Y(f"{self.settings['y']}:O",              
                axis=alt.Axis(title="year"),
            ),
            color = f"{self.settings['color']}",
            tooltip=[self.settings['x'], self.settings['y'], self.settings['color']]
        )

        return fig.properties(width=self.settings['width'],height = self.settings['height'], title = self.settings['title'])


    def generate_plot(self, df):
        def fill_missing_months_with_zero(df):
            for m in range(1,13):
                df=df.append({'location_id': df.iloc[0]['location_id'], 'month':m},ignore_index=True)
            return df

        def fill_missing_years_with_zero(df):
            for y in range(self.settings['year_from'],self.settings['year_from']+1):
                df=df.append({'location_id': df.iloc[0]['location_id'], 'year':y},ignore_index=True)
            return df

        def fill_missing_weeks_with_zero(df):
            for w in range(1,52):
                df=df.append({'location_id': df.iloc[0]['location_id'], 'week':w},ignore_index=True)
            return df
        
        def fill_missing_month_year_with_zero(df):
            for m in range(1,13):
                for y in range(self.settings['year_from'],self.settings['year_from']+1):
                    df=df.append({'location_id': df.iloc[0]['location_id'], 'month':m, 'year':y},ignore_index=True)
            return df

        def fill_missing_week_year_with_zero(df):
            for w in range(1,52):
                for y in range(self.settings['year_from'],self.settings['year_from']+1):
                    df=df.append({'location_id': df.iloc[0]['location_id'], 'week':w, 'year':y},ignore_index=True)
            return df

        if self.settings['plottype']=='barchart':
            self.settings['size'] = 20
            self.settings['x_data_type']=''
            title_prefix = ''
            if self.settings['time_agg'] == 'day':        
                title_prefix = 'Precipitation at station'
                self.settings['size'] = 1            
                df = df[['location_id','date','AccumulationFinal']]
                self.settings['x'] = 'date'
                self.settings['y'] = 'AccumulationFinal'
            elif self.settings['time_agg'] == 'week':     
                title_prefix = 'Average weekly precipitation at station'
                self.settings['size'] = 10        
                df = fill_missing_weeks_with_zero(df)            
                df = df[['location_id','week','AccumulationFinal']].groupby(['location_id', 'week']).agg('sum').reset_index()      

                self.settings['x'] = 'week'
                self.settings['y'] = 'AccumulationFinal'
            elif self.settings['time_agg'] == 'month':
                title_prefix = 'Average monthly precipitation at station'
                df = fill_missing_months_with_zero(df)
                    
                df = df[['location_id','month','AccumulationFinal']].groupby(['location_id', 'month']).agg('sum').reset_index()      
                df['AccumulationFinal'] = df['AccumulationFinal'] / (self.settings['year_to']-self.settings['year_from']+1)
                self.settings['x'] = 'month'
                self.settings['y'] = 'AccumulationFinal'
                df['month'] = df['month'].replace(cn.MONTH_DICT)
            elif self.settings['time_agg'] == 'year':     
                df = fill_missing_years_with_zero(df)
                self.settings['x_data_type']=':O'    
                title_prefix = 'Average yearly precipitation at station'           
                df = df[['location_id','year','AccumulationFinal']].groupby(['location_id', 'year']).agg('sum').reset_index()      
                
                self.settings['x'] = 'year'
                self.settings['y'] = 'AccumulationFinal'
            self.settings['title'] = f"{title_prefix} {self.settings['title']}"
            fig = self.plot_barchart(df)
        elif self.settings['plottype']=='heatmap':
            self.settings['x_data_type']=''
            title_prefix = ''
            self.settings['color'] = 'AccumulationFinal'
            self.settings['y'] = 'year'
            if self.settings['time_agg'] == 'week':     
                title_prefix = 'Average weekly precipitation at station'      
                df = fill_missing_week_year_with_zero(df)          
                df = df[['location_id','year','week','AccumulationFinal']].groupby(['location_id','year','week']).agg('sum').reset_index()      
                self.settings['x'] = 'week'
            elif self.settings['time_agg'] == 'month':
                title_prefix = 'Average monthly precipitation at station'
                df = fill_missing_month_year_with_zero(df)                     
                df = df[['location_id','year','month','AccumulationFinal']].groupby(['location_id', 'year', 'month']).agg('sum').reset_index()      
                self.settings['x'] = 'month'
                df['month'] = df['month'].replace(cn.MONTH_DICT)
        
            fig = self.plot_heatmap(df)
        return fig


    def show_plot(self):            
        for station in self.settings['stations']:
            self.settings['title'] = f"{station} ({self.settings['year_from']} - {self.settings['year_to']})"
            df = self.df_stations[self.df_stations['PGMN_WELL'] == station] 
            location_id = int(df.iloc[0]['location_id'])
            df_prec = self.df_precipitation[self.df_precipitation['location_id'] == location_id] 
            df_prec = df_prec[ (df_prec['year']>= self.settings['year_from']) & (df_prec['year']<= self.settings['year_to']) ]
            if not df_prec.empty:
                self.settings['title'] = f"{station} ({self.settings['year_from']} - {self.settings['year_to']})"
                fig = self.generate_plot(df_prec)
                st.altair_chart(fig)


    def show_menu(self):
        def get_stations():
            df =  self.df_stations
            if len(self.settings['cons_authorities']) > 0:
                filter = df['CONS_AUTHO'].isin(self.settings['cons_authorities']) 
                df =  self.df_stations[filter]

            stations = list(df['PGMN_WELL'])
            stations.sort()
            return stations


        def show_plot_types():
            self.settings['plottype'] = st.sidebar.selectbox("Plot type", list(dic_plottypes.keys()),
                format_func=lambda x: dic_plottypes[x])
            self.settings['time_agg'] = st.sidebar.selectbox("Time aggregation", time_aggregation[self.settings['plottype']])
            
            self.settings['width'] = st.sidebar.number_input('Plot width (px)', value=800,min_value=100,max_value=10000)
            self.settings['height']= st.sidebar.number_input('Plot height (px)', value=300,min_value=100,max_value=10000)
            

        def show_filter():
            default=[self.lst_conservation_authorities[0]]
            self.settings['cons_authorities'] = st.sidebar.multiselect("🔎 Conservation authority", self.lst_conservation_authorities, [])
            default=[self.lst_aquifer[0]]
            lst_stations = get_stations()
            default = [lst_stations[0]]
            self.settings['stations'] = st.sidebar.multiselect("🎯 Station", lst_stations, default)
            self.settings['year_from'], self.settings['year_to'] = st.sidebar.select_slider("Years", range(first_year,current_year),[current_year-6,current_year-1])
           
        show_filter()
        show_plot_types()
        self.show_plot()
    

