
import pandas as pd
import streamlit as st
import numpy as np
import pydeck as pdk
from st_aggrid import AgGrid

import const as cn
import tools

colors = cn.COLOR_SCHEMAS['rainbow tones']
class App:
    def __init__(self, df_stations, df_waterlevels, df_precipitation, df_wl_stations, df_precipitation_stations):
        self.df_stations = df_stations[df_stations['LATITUDE'] != 0]  #only stations with coordinates
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

    
    def get_numerical_legend(self, min_val: float, max_val: float, height: int):
        """
        Renders the map plot blue-green gradient legend showing 2 circles and the corresponding intervals. Eg. values
        go from 100 to 500 in a map. Then values vom 100-349 will be shown in blue shades, 350-500 in green shades.

        :param min_val: minimum value in plot
        :param max_val: maximum value in plot
        :param height: height of circle
        :return: None
        """

        a = round(min_val)
        b = round(min_val + (max_val - min_val) / 2)
        c = round(max_val)
        legend = """
        <style>
        .bdot {{
        height: {0}px;
        width: {0}px;
        background-color: Blue;
        border-radius: 50%;
        display: inline-block;
        }}
        .gdot {{
        height: {0}px;
        width: {0}px;
        background-color: #4DFF00;
        border-radius: 50%;
        display: inline-block;
        }}
        .rdot {{
        height: {0}px;
        width: {0}px;
        background-color: #FF0000;
        border-radius: 50%;
        display: inline-block;
        }}
        </style>
        <div style="text-align:left">
        <h3>Legend</h3>
        <span class="bdot"></span>  {1} - {2}<br>
        <span class="gdot"></span>  &#62;{2} - {3}<br>
        <span class="rdot"></span>  &#62;{3}
        </div>
        """.format(height, a, b, c)
        return legend
    
    def get_categorical_legend(self, categories: dict):
        """
        Renders the map plot blue-green gradient legend showing 2 circles and the corresponding intervals. Eg. values
        go from 100 to 500 in a map. Then values vom 100-349 will be shown in blue shades, 350-500 in green shades.

        :param categories: format {'name': 'bedrock', 'color':'red', 'size': 10}
        :param max_val: maximum value in plot
        :param height: height of circle
        :return: None
        """

        style = "<style>"
        for key, value in categories.items():
            style += f"""
                .{key} {{
                height: {value['size']}px;
                width: {value['size']}px;
                background-color: {value['color']};
                border-radius: 50%;
                display: inline-block;
            }}"""
        style += "</style>"
        legend = """<div style="text-align:left"><h3>Legend</h3>"""
        for key, value in categories.items():
            legend += f"""<span class="{key}"></span>&nbsp;{key}<br>"""
            
        legend += "</div>"
        return style + legend
    
    def plot_map(self, df: pd.DataFrame, settings: dict):
        """
        layer_type: str, value_col: str, tooltip_html: str

        Generates a map plot

        :param value_col: column holding parameter to be plotted
        :param layer_type: HexagonLayer or ScatterplotLayer
        :param title: title of plot
        :param df: dataframe with data to be plotted
        :return:
        """
        
        if df.shape[0] > 0:
            #df = df[['LONGITUDE','LATITUDE']]
            midpoint = (np.average(df[settings['latitude_column']]), np.average(df[settings['longitude_column']]))
            st.markdown("### {}".format(settings['title']))
            
            icon_data = {
                "url": "https://img.icons8.com/plasticine/100/000000/marker.png",
                "width": 128,
                "height": 128,
                "anchorY": 128
            }
            position = f"[{settings['longitude_column']}, {settings['latitude_column']}]"
            if settings['value_col']:
                min_val: float = df[settings['value_col']].min()
                max_val: float = df[settings['value_col']].quantile(0.9)
                df["color_r"] = df.apply(lambda row: tools.color_gradient(row, settings['value_col'], min_val, max_val, 'r'), axis=1)
                df["color_g"] = df.apply(lambda row: tools.color_gradient(row, settings['value_col'], min_val, max_val, 'g'), axis=1)
                df["color_b"] = df.apply(lambda row: tools.color_gradient(row, settings['value_col'], min_val, max_val, 'b'), axis=1)
            

            if settings['layer_type'] == 'HexagonLayer':
                layer = pdk.Layer(
                    type='HexagonLayer',
                    data=df,
                    get_position=position,
                    auto_highlight=True,
                    elevation_scale=50,
                    pickable=True,
                    elevation_range=[0, 3000],
                    extruded=True,
                    coverage=1,
                    getFillColor="color",#"[color_r, color_g, color_b, color_a]",
                )
            elif settings['layer_type'] == 'ScatterplotLayer':
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    df,
                    pickable=True,
                    opacity=0.7,
                    stroked=True,
                    filled=True,
                    radius_scale=6,
                    radius_min_pixels=1,
                    radius_max_pixels=100,
                    line_width_min_pixels=1,
                    get_position=position,
                    get_radius=400,
                    getFillColor="[color_r, color_g, color_b, color_a]",
                    get_line_color=[0, 0, 0],
                )
            elif settings['layer_type'] == 'IconLayer':
                df['icon_data'] = str(icon_data)
                layer = pdk.Layer(
                    settings['layer_type'],
                    df,
                    get_icon='icon_data',
                    pickable=True,
                    size_scale=20,
                    get_position=position,
                )
            
            view_state = pdk.ViewState(
                longitude=midpoint[1], latitude=midpoint[0], zoom=6, min_zoom=5, max_zoom=15, pitch=0, bearing=-27.36
            )
            map = pdk.Deck(
                map_style=cn.MAPBOX_STYLE,
                layers=[layer],
                initial_view_state=view_state,
                tooltip={
                    "html":settings['tooltip_html'],
                    "style": {'fontSize': cn.TOOLTIP_FONTSIZE,
                        "backgroundColor": cn.TOOLTIP_BACKCOLOR,
                        "color": cn.TOOLTIP_FORECOLOR}
                }
            )
            st.pydeck_chart(map)

            if settings['legend']:
                st.markdown(settings['legend'], unsafe_allow_html=True)
            if settings['show_data_table']:
                df = tools.remove_nan_columns(df)
                df = tools.remove_columns(df, ['color_r', 'color_g', 'color_b'])
                # df = df.rename(columns={'calc_value': title})
                st.dataframe(df)
                st.markdown(tools.get_table_download_link(df), unsafe_allow_html=True)
        else:
            st.warning('Unable to create map: no location data was found')

    def show_menu(self):
        
        def get_stations():
            df =  self.df_stations
            if len(self.settings['cons_authorities']) > 0:
                filter = df['CONS_AUTHO'].isin(self.settings['cons_authorities']) 
                df =  self.df_stations[filter]
            
            if len(self.settings['aquifer_types']):
                filter = df['AQUIFER_TY'].isin(self.settings['aquifer_types'])
                df =  df[filter]
            
            lst_stations = list(pd.to_numeric(df['location_id'].unique()))
            field_list = ['PGMN_WELL','location_id','CONS_AUTHO','COUNTY','TOWNSHIP','LOT','CONCESSION','AQUIFER_LI', 'AQUIFER_TY', 'WELL_DEPTH','WEL_PIEZOM','SCREEN_HOL','LATITUDE','LONGITUDE','ELEV_GROUN']
            df = df[field_list]
            return df, lst_stations
        
        def get_map_data(map_parameter, lst_filtered_stations, filtered_stations):
            settings={}
            if map_parameter.lower() == 'wells by aquifer type':
                fields = ['PGMN_WELL','location_id','LONGITUDE','LATITUDE', 'AQUIFER_TY', 'WELL_DEPTH','SCREEN_HOL','ELEV_GROUN','COUNTY','TOWNSHIP','CONS_AUTHO']
                filtered_stations = filtered_stations[fields]
                df_locations = filtered_stations[filtered_stations['AQUIFER_TY'].notnull()]
                # na
                df_locations["color_r"] = colors['LightGray']['r']
                df_locations["color_g"] = colors['LightGray']['g']
                df_locations["color_b"] = colors['LightGray']['b']
                #bedrock wells
                df_locations.loc[df_locations['AQUIFER_TY'] == 'BEDROCK', 'color_r'] = colors['red']['r']
                df_locations.loc[df_locations['AQUIFER_TY'] == 'BEDROCK', 'color_g'] = colors['red']['g']
                df_locations.loc[df_locations['AQUIFER_TY'] == 'BEDROCK', 'color_b'] = colors['red']['b']
                #overburden wells
                df_locations.loc[df_locations['AQUIFER_TY'] == 'OVERBURDEN', 'color_r'] = colors['sapphire']['r']
                df_locations.loc[df_locations['AQUIFER_TY'] == 'OVERBURDEN', 'color_g'] = colors['sapphire']['g']
                df_locations.loc[df_locations['AQUIFER_TY'] == 'OVERBURDEN', 'color_b'] = colors['sapphire']['b']
                #interface wells
                df_locations.loc[df_locations['AQUIFER_TY'] == 'INTERFACE', 'color_r'] = colors['indigo']['r']
                df_locations.loc[df_locations['AQUIFER_TY'] == 'INTERFACE', 'color_g'] = colors['indigo']['g']
                df_locations.loc[df_locations['AQUIFER_TY'] == 'INTERFACE', 'color_b'] = colors['indigo']['b']

                settings['tooltip_html'] = """
                    <b>Station:</b> {PGMN_WELL}<br/>
                    <b>Ground elev:</b> {ELEV_GROUN}masl<br/>
                    <b>County:</b> {COUNTY}<br/>
                    <b>Township:</b> {TOWNSHIP}<br/>
                    <b>Conservation Authority:</b> {CONS_AUTHO}<br/>
                    <b>Aquifer type:</b> {AQUIFER_TY}<br/>
                    <b>Well depth:</b> {WELL_DEPTH}m<br/>
                    {SCREEN_HOL}<br/>                    
                """
                categories = {}
                categories['Bedrock'] = {'color':colors['red']['hex'], 'size': 10}
                categories['Overburden'] = {'color':colors['sapphire']['hex'], 'size': 10}
                categories['Interface'] = {'color':colors['indigo']['hex'], 'size': 10}
                categories['NA'] = {'color':colors['LightGray']['hex'], 'size': 10}

                settings['legend'] = self.get_categorical_legend(categories)
                settings['value_col'] = None
            return df_locations, settings, categories

        def show_filter():
            self.settings['cons_authorities'] = st.sidebar.multiselect("🔎 Conservation authority", self.lst_conservation_authorities)
            self.settings['aquifer_types'] = st.sidebar.multiselect("🔎 Aquifer types", self.lst_aquifer)
        
        show_filter()

        filtered_stations, lst_stations = get_stations()
        lst_parameters = ['wells by aquifer type']
        map_parameter = st.sidebar.selectbox('Symbol color', lst_parameters)
        df, settings, categories = get_map_data(map_parameter, lst_stations, filtered_stations)
        settings['latitude_column'] = cn.LATITUDE_COLUMN
        settings['longitude_column'] = cn.LONGITUDE_COLUMN
        settings['layer_type'] = 'ScatterplotLayer' 
        settings['title'] = map_parameter
        settings['show_data_table'] = False
        fig = self.plot_map(df, settings)
        if fig:
            st.write(fig)

    

