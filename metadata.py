import pandas as pd
import streamlit as st
#import tools
#import numpy as np

LATITUDE_COLUMN = 'LATITUDE'
LONGITUDE_COLUMN = 'LONGITUDE'
MAP_LEGEND_SYMBOL_SIZE: int = 10
MAPBOX_STYLE: str = "mapbox://styles/mapbox/light-v10"
GRADIENT: str = 'blue-green'
TOOLTIP_FONTSIZE = 'x-small'
TOOLTIP_BACKCOLOR = 'white'
TOOLTIP_FORECOLOR = 'black'

class App:
    def __init__(self, data_frames, df_station):
        self.data_frames = data_frames
        self.df_station = df_station
        self.settings = {}
        self.lst_conservation_authorities = ['<all>'] + list(df_station['CONS_AUTHO'].unique())
        self.lst_aquifer = ['<all>'] + list(df_station['AQUIFER_TY'].unique())
        self.stations = []
        self.PLOTS = ['timeseries', 'bartchart ', 'map']
        self.AGGREGATE_TIME = ['month','year']

    
    def show_menu(self):
        def get_stats(df):
            stat_df = pd.DataFrame()
            for station in list(df['PGMN_WELL']):
                _df = self.data_frames[station]
                _df = _df[['CASING_ID','year','wl_elev']]
                agg_df = _df.groupby('CASING_ID').agg(
                    year_min=pd.NamedAgg(column="year", aggfunc="min"),
                    year_max=pd.NamedAgg(column="year", aggfunc="max"),
                    wl_elev_min=pd.NamedAgg(column="wl_elev", aggfunc="min"),
                    wl_elev_max=pd.NamedAgg(column="wl_elev", aggfunc="max"),
                    wl_elev_mean=pd.NamedAgg(column="wl_elev", aggfunc="mean"),
                    wl_elev_std=pd.NamedAgg(column="wl_elev", aggfunc="std")
                ).reset_index()
                stat_df = stat_df.append(agg_df)
        
            stat_df = stat_df.reset_index().drop('index', axis=1)
            return stat_df

        def get_stations():
            df =  self.df_station
            if self.settings['cons_authorities'] != []:
                filter = df['CONS_AUTHO'].isin(self.settings['cons_authorities']) 
                df =  self.df_station[filter]
            
            if self.settings['aquifer_types'] != []:
                filter = df['AQUIFER_TY'].isin(self.settings['aquifer_types'])
                df =  df[filter]
            
            field_list = ['PGMN_WELL','CONS_AUTHO','COUNTY','TOWNSHIP','LOT','CONCESSION','AQUIFER_LI', 'WELL_DEPTH','WEL_PIEZOM','SCREEN_HOL','LATITUDE','LONGITUDE','ELEV_GROUN']
            
            df = df[field_list]

            return df

        def show_filter():
            self.settings['cons_authorities'] = st.sidebar.multiselect("Conservation authority", self.lst_conservation_authorities, [])
            self.settings['aquifer_types'] = st.sidebar.multiselect("Aquifer types", self.lst_aquifer, [])
        
        st.write(self.df_station )
        show_filter()
        stations = get_stations()
        st.markdown('### Metadata')
        st.write(stations)
        st.markdown('### Statistics')
        stats = get_stats(stations)
        st.write(stats)

        # self.plot_map('stations', stations, 'ScatterplotLayer', 'WELL_DEPTH')

    

