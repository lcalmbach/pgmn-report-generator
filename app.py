from __future__ import print_function
import pandas as pd
import streamlit as st
import os

from streamlit.caching import get_cache_path

import pgmn_metadata
import pgmn_report_generator
import pgmn_wl_explorer
import pgmn_prec_explorer
import pgmn_info as info
import pgmn_maps as maps


__version__ = '0.0.11' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-05-20'
my_name = 'PGMN waterlevels'
my_kuerzel = "PWD"
GIT_REPO = 'https://github.com/lcalmbach/pgmn-report-generator'
conn = {}
config = {} # dictionary mit allen Konfigurationseinträgen
APP_INFO = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    <a href="{GIT_REPO}">git-repo</a>
    """

MENU_DIC = {info: 'Info', 
    pgmn_metadata: 'Metadata on wells', 
    maps: 'Maps', 
    pgmn_wl_explorer: 'Explore water levels', 
    pgmn_prec_explorer: 'Explore precipitation data', 
    pgmn_report_generator: 'Generate pdf reports'}

BASE_DATA = os.path.join(os.getcwd(), 'static','data')
BASE_PRECIPITATION = os.path.join(os.getcwd(), 'static','data', 'precipitation')
PRECIPITATION_FILE = os.path.join(os.getcwd(), 'static','data', 'daily_prec.csv')
WL_FILE = os.path.join(os.getcwd(), 'static','data', 'daily_wl.zip')
BASE_WATER_LEVELS = os.path.join(os.getcwd(), 'static','data', 'water_levels')
CSS_STYLE_FILE = './style.css'
STATION_FILE = os.path.join(BASE_DATA, 'PGMN_WELLS_NAD83.csv') 

@st.cache()
def get_data():
    def get_station_data():
        df = pd.read_csv(STATION_FILE, sep=';')
        df['location_id'] = pd.to_numeric(df['PGMN_WELL'].str[3:8])
        pd.to_numeric(df['location_id'])        
        return df

    def get_wl_data():
        df = pd.read_csv(WL_FILE, sep=';')     
        df['date'] = pd.to_datetime(df['date'])    
        df['week'] = df['date'].dt.isocalendar().week
        df['mid_week_date'] = pd.to_datetime(df['date']) - pd.to_timedelta(df['date'].dt.dayofweek % 7 - 2, unit='D')
        df['mid_week_date'] = df['mid_week_date'].dt.date 
        df['year'] = df['date'].dt.year    
        df['month'] = df['date'].dt.month  
        df['location_id'] = pd.to_numeric(df['CASING_ID'].str[5:8])  
        return df

    def get_preciptiation_data():
        df = pd.read_csv(PRECIPITATION_FILE, sep=';')
        df['date'] = pd.to_datetime(df['date'])    
        df['week'] = df['date'].dt.isocalendar().week
        df['mid_week_date'] = pd.to_datetime(df['date']) - pd.to_timedelta(df['date'].dt.dayofweek % 7 - 2, unit='D')
        df['mid_week_date'] = df['mid_week_date'].dt.date 
        df['year'] = df['date'].dt.year    
        df['month'] = df['date'].dt.month
        df['location_id'] = pd.to_numeric(df['location_id'])  
        return df

    def get_wl_stations(df_stations:pd.DataFrame, df_wl:pd.DataFrame)-> pd.DataFrame:
        lst_wl_stations = list(df_wl['CASING_ID'].unique())
        df = df_stations[ df_stations['PGMN_WELL'].isin(lst_wl_stations)]
        return df

    def get_precipitation_stations(df_stations:pd.DataFrame, df_precipitation:pd.DataFrame)-> pd.DataFrame:
        lst_precipitation_stations = list(df_precipitation['location_id'].unique())
        df = df_stations[ df_stations['location_id'].isin(lst_precipitation_stations)]
        return df

    df_stations = get_station_data()
    df_wl = get_wl_data()
    df_wl_stations = get_wl_stations(df_stations, df_wl)
    df_precipitation = get_preciptiation_data()
    df_precipitation_stations = get_precipitation_stations(df_stations, df_precipitation)
    
    return df_stations, df_wl, df_precipitation, df_wl_stations, df_precipitation_stations
    

def main():
    st.set_page_config(
    page_title=my_name,
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded")
    st.sidebar.markdown("### 🌍 PGMN water levels")
    df_stations, df_waterlevels, df_precipitation, df_wl_stations, df_precipitation_stations = get_data()
    my_app = st.sidebar.selectbox("Application", options=list(MENU_DIC.keys()),
        format_func=lambda x: MENU_DIC[x])
    app = my_app.App(df_stations, df_waterlevels, df_precipitation, df_wl_stations, df_precipitation_stations)
    app.show_menu()
    st.sidebar.markdown(APP_INFO, unsafe_allow_html=True)
if __name__ == "__main__":
    main()

