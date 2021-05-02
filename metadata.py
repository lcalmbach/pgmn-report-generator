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
    def __init__(self, data_frames, df_station):
        self.data_frames = data_frames
        self.df_station = df_station
        self.settings = {}
        self.lst_conservation_authorities = ['<all>'] + list(df_station['CONS_AUTHO'].unique())
        self.lst_aquifer = ['<all>'] + list(df_station['AQUIFER_TY'].unique())
        self.stations = []
        self.PLOTS = ['timeseries', 'bartchart ', 'map']
        self.AGGREGATE_TIME = ['month','year']

    
    def plot_map(self, title: str, df: pd.DataFrame, layer_type: str, value_col: str):
        """
        Generates a map plot

        :param value_col: column holding parameter to be plotted
        :param layer_type: HexagonLayer or ScatterplotLayer
        :param title: title of plot
        :param df: dataframe with data to be plotted
        :return:
        """

        if df.shape[0] > 0:
            midpoint = (np.average(df[LATITUDE_COLUMN]), np.average(df[LONGITUDE_COLUMN]))
            #st.markdown("### {title}")
            st.write(456)
            icon_data = {
                "url": "https://img.icons8.com/plasticine/100/000000/marker.png",
                "width": 128,
                "height": 128,
                "anchorY": 128
            }
            st.write(123)
            if value_col:
                min_val: float = df[value_col].min()
                max_val: float = df[value_col].quantile(0.9)
                df["color_r"] = df.apply(lambda row: tools.color_gradient(row, value_col, min_val, max_val, 'r'), axis=1)
                df["color_g"] = df.apply(lambda row: tools.color_gradient(row, value_col, min_val, max_val, 'g'), axis=1)
                df["color_b"] = df.apply(lambda row: tools.color_gradient(row, value_col, min_val, max_val, 'b'), axis=1)
            else:
                df["color_r"] = 255
                df["color_g"] = 0
                df["color_b"] = 0

            if layer_type == 'HexagonLayer':
                layer = pdk.Layer(
                    type='HexagonLayer',
                    data=df,
                    get_position=f"[{LONGITUDE_COLUMN}, {LATITUDE_COLUMN}]",
                    auto_highlight=True,
                    elevation_scale=50,
                    pickable=True,
                    elevation_range=[0, 3000],
                    extruded=True,
                    coverage=1,
                    getFillColor="[color_r, color_g, color_b, color_a]",
                )
            elif layer_type == 'ScatterplotLayer':
                layer = pdk.Layer(
                    type='ScatterplotLayer',
                    data=df,
                    pickable=True,
                    get_position=f"[LONGITUDE,LATITUDE_COLUMN]",
                    radius_scale=4,
                    radius_min_pixels=4,
                    radius_max_pixels=10,
                    getFillColor="[color_r, color_g, color_b]",
                )
            elif layer_type == 'IconLayer':
                df['icon_data'] = None
                for i in df.index:
                    df['icon_data'][i] = icon_data
                layer = pdk.Layer(
                    type='IconLayer',
                    data=df,
                    get_icon='icon_data',
                    pickable=True,
                    size_scale=20,
                    get_position=f"[LONGITUDE,LATITUDE_COLUMN]",
                )
            view_state = pdk.ViewState(
                longitude=midpoint[1], latitude=midpoint[0], zoom=6, min_zoom=5, max_zoom=15, pitch=0, bearing=-27.36
            )
            r = pdk.Deck(
                map_style=MAPBOX_STYLE,
                layers=[layer],
                initial_view_state=view_state,
                tooltip={
                    "html": '', #tooltip_html
                    "style": {'fontSize': TOOLTIP_FONTSIZE,
                        "backgroundColor": TOOLTIP_BACKCOLOR,
                        "color": TOOLTIP_FORECOLOR}
                }
            )

            st.pydeck_chart(r)
            if value_col:
                self.render_legend(min_val, max_val, MAP_LEGEND_SYMBOL_SIZE)
            if self.show_data_table:
                df = tools.remove_nan_columns(df)
                df = tools.remove_columns(df, ['color_r', 'color_g', 'color_b'])
                # df = df.rename(columns={'calc_value': title})
                st.dataframe(df)
                st.markdown(tools.get_table_download_link(df), unsafe_allow_html=True)
        else:
            st.warning('Unable to create map: no location data was found')
            

    def show_menu(self):

        @st.cache(persist=True)
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
        
        show_filter()
        stations = get_stations()
        st.markdown('### Metadata')
        st.write(stations)
        st.markdown('### Statistics')
        stats = get_stats(stations)
        st.write(stats)

        # self.plot_map('stations', stations, 'ScatterplotLayer', 'WELL_DEPTH')

    

