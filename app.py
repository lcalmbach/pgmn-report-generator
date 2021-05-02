from __future__ import print_function
import pandas as pd
import streamlit as st
import os
import glob

import metadata
import pgmn_report_generator
import pgmn_explorer

__version__ = '0.0.6' 
__author__ = 'lukas calmbach'
__author_email__ = 'lukas.calmbach@bs.ch'
version_date = '2021-04-30'
my_name = 'PGMN waterlevel data'
my_kuerzel = "PWD"
conn = {}
config = {} # dictionary mit allen Konfigurationseinträgen
MENU_DIC = {metadata: 'Metadata on wells', pgmn_explorer: 'Explore water level data', pgmn_report_generator: 'Generate pdf reports'}

TABLE_TEMPLATE_FILE = "table_template.html"
FIG_TEMPLATE_FILE = "figure_template.html"
BASE_HTML = os.path.join(os.getcwd(), 'html')
BASE_PDF = os.path.join(os.getcwd(), 'pdf')
BASE_FIG = os.path.join(os.getcwd(), 'images')
BASE_DATA = os.path.join(os.getcwd(), 'data')
PDF_TARGET_FILE = os.path.join(BASE_PDF, 'output.pdf') #f"./pdf/output.pdf"
CSS_STYLE_FILE = './style.css'
STATION_FILE = os.path.join(BASE_DATA, 'PGMN_WELLS_NAD83.csv') #'./test_data/PGMN_WELLS_NAD83.csv'


@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_data():
    data_frames = {}
    df_stations = pd.DataFrame()
    rows = 0
    info = st.empty()
    
    df_stations = pd.read_csv(STATION_FILE, sep=';')
    file_list = glob.glob(f"{BASE_DATA}\*.zip")
    for f in file_list:
        info.write(f"reading file {f}")
        try:
            df = pd.read_csv(f, sep=",")
            df = df.rename(columns={'READING_DTTM':'date', 'Water_Level_Elevation_meter_above_sea_level': 'wl_elev'})
            df['date'] = pd.to_datetime(df['date'])    
            df['year'] = df['date'].dt.year    
            df['month'] = df['date'].dt.month    
            rows += len(df)
            station = df.iloc[0]['CASING_ID']
            data_frames[station] = df
        except Exception as ex:
            print(f'error in {f}:{ex}')

    piezo_stations = list(data_frames.keys())
    df_stations = df_stations[df_stations['PGMN_WELL'].isin(piezo_stations)]
    
    return data_frames, df_stations
    
def display_app_info():
    """
    Zeigt die Applikations-Infos sowie Kontaktdaten bei Fragen in einer Info-box in der sidebar an.
    """

    text = f"""
    <style>
        #appinfo {{
        font-size: 11px;
        background-color: lightblue;
        padding-top: 10px;
        padding-right: 10px;
        padding-bottom: 10px;
        padding-left: 10px;
        border-radius: 10px;
    }}
    </style>
    <div id ="appinfo">
    App: {my_name}<br>
    App-Version: {__version__} ({version_date})<br>
    Implemented by Lukas Calmbach using Python, <a href="https://streamlit.io/">Streamlit</a>, and pdfkit<br>
    <a href="https://github.com/lcalmbach/pgmn-report-generator">git-repo</a><br>
    </div>
    """
    st.sidebar.markdown(text, unsafe_allow_html=True)

def main():
    st.sidebar.markdown("### 🌍 PGMN water levels")
    data_frames, df_stations = get_data()

    my_app = st.sidebar.selectbox("Application", options=list(MENU_DIC.keys()),
    format_func=lambda x: MENU_DIC[x])
    app = my_app.App(data_frames, df_stations)
    app.show_menu()
    display_app_info()  

if __name__ == "__main__":
    main()

