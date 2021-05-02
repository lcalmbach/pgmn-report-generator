from __future__ import print_function
import pandas as pd
import streamlit as st
import tools
import pydeck as pdk
import numpy as np

LATITUDE_COLUMN = 'LATITUDE'
LONGITUDE_COLUMN = 'LONGITUDE'
MAP_LEGEND_SYMBOL_SIZE: int = 10
MAPBOX_STYLE: str = "mapbox://styles/mapbox/light-v10"
GRADIENT: str = 'blue-green'
TOOLTIP_FONTSIZE = 'x-small'
TOOLTIP_BACKCOLOR = 'white'
TOOLTIP_FORECOLOR = 'black'

class App:
    def __init__(self, df_station):
        self.df_station = df_station
        

    def show_menu(self):
        st.write(self.df_station)


    

