
import pandas as pd
import streamlit as st
#import tools
import numpy as np
from st_aggrid import AgGrid

LATITUDE_COLUMN = 'LATITUDE'
LONGITUDE_COLUMN = 'LONGITUDE'
MAP_LEGEND_SYMBOL_SIZE: int = 10
MAPBOX_STYLE: str = "mapbox://styles/mapbox/light-v10"
GRADIENT: str = 'blue-green'
TOOLTIP_FONTSIZE = 'x-small'
TOOLTIP_BACKCOLOR = 'white'
TOOLTIP_FORECOLOR = 'black'

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
        self.PLOTS = ['timeseries', 'bartchart ', 'map']
        self.AGGREGATE_TIME = ['month','year']

    
    def show_menu(self):
        def get_wl_stats(df):
            _df = self.df_waterlevels[['CASING_ID','location_id','year','wl_elev']]
            stat_df = _df.groupby(['CASING_ID','location_id']).agg(
                first_year=pd.NamedAgg(column="year", aggfunc="min"),
                last_year=pd.NamedAgg(column="year", aggfunc="max"),
                wl_elev_min=pd.NamedAgg(column="wl_elev", aggfunc="min"),
                wl_elev_max=pd.NamedAgg(column="wl_elev", aggfunc="max"),
                wl_elev_mean=pd.NamedAgg(column="wl_elev", aggfunc="mean"),
                wl_elev_std=pd.NamedAgg(column="wl_elev", aggfunc="std")
            ).reset_index()

            stat_df = stat_df.reset_index().drop('index', axis=1)
            return stat_df

        def get_precipitation_stats():
            stat_df = pd.DataFrame()
            _base_df = self.df_precipitation.groupby(['LocationWell', 'location_id', 'year']).agg(
                prec=pd.NamedAgg(column="AccumulationFinal", aggfunc="sum"),
            ).reset_index()

            stat_df = _base_df.groupby(['LocationWell', 'location_id']).agg(
                first_year=pd.NamedAgg(column="year", aggfunc="min"),
                last_year=pd.NamedAgg(column="year", aggfunc="max"),
                min=pd.NamedAgg(column="prec", aggfunc="min"),
                max=pd.NamedAgg(column="prec", aggfunc="max"),
                mean=pd.NamedAgg(column="prec", aggfunc="mean"),
                std=pd.NamedAgg(column="prec", aggfunc="std"),
            )

            stat_df = stat_df.reset_index()
            return stat_df

        def get_stations():
            df =  self.df_stations
            if len(self.settings['cons_authorities']) > 0:
                filter = df['CONS_AUTHO'].isin(self.settings['cons_authorities']) 
                df =  self.df_stations[filter]
            
            if len(self.settings['aquifer_types']):
                filter = df['AQUIFER_TY'].isin(self.settings['aquifer_types'])
                df =  df[filter]
            
            lst_stations = list(pd.to_numeric(df['location_id'].unique()))
            field_list = ['PGMN_WELL','CONS_AUTHO','COUNTY','TOWNSHIP','LOT','CONCESSION','AQUIFER_LI', 'WELL_DEPTH','WEL_PIEZOM','SCREEN_HOL','LATITUDE','LONGITUDE','ELEV_GROUN']
            df = df[field_list]
            return df, lst_stations

        def show_filter():
            self.settings['cons_authorities'] = st.sidebar.multiselect("🔎 Conservation authority", self.lst_conservation_authorities)
            self.settings['aquifer_types'] = st.sidebar.multiselect("🔎 Aquifer types", self.lst_aquifer)
        
        show_filter()
        stations, lst_stations = get_stations()
        with st.beta_expander(f'All Stations ({len(stations)})'):
            AgGrid(stations)
        stats = get_wl_stats(stations)
        stats = stats[stats['location_id'].isin(lst_stations)]
        with st.beta_expander(f"Water levels statistics ({ len(pd.unique(stats['CASING_ID'])) } stations)"):
            AgGrid(stats)
        stats = get_precipitation_stats()
        stats = stats[stats['location_id'].isin(lst_stations)]
        
        with st.beta_expander(f"Precipitation statistics ({ len(pd.unique(stats['LocationWell'])) } stations)"):
            stats['min'] = stats['min'].apply('{:.2f}'.format)
            stats['max'] = stats['max'].apply('{:.2f}'.format)
            stats['mean'] = stats['mean'].apply('{:.2f}'.format)
            stats['std'] = stats['std'].apply('{:.2f}'.format)
            AgGrid(stats)

        # self.plot_map('stations', stations, 'ScatterplotLayer', 'WELL_DEPTH')

    

