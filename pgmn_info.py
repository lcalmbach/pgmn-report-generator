import streamlit as st

text = """The PGMN is a network of over {} wells across 38 watersheds in Ontario that record data on groundwater quality and quantity. {} wells
are equipped with piezometers and {} wells with rain gauges. Water quality samples are also collected from some wells, but this data has not yet been included in this app.<br>
The data collected assists in determining groundwater quality and aquifer extents across the province with the goal of assuring safe 
drinking water supplies and will complement knowledge gained through the regional groundwater studies. 
<br><br>
The network also provides an early warning system for changes in water levels caused by climate conditions or human activities and information on regional trends in groundwater quality. 
The groundwater level readings are taken hourly and are stored in a datalogger for either manual or remote automated download. 
The downloaded data is maintained by the MOE and is made available for use by the partner Conservation Authorities. All data can be downloaded from [Ontario Data Catalogue](https://www.ontario.ca/environment-and-energy/map-provincial-groundwater-monitoring-network)
<br><br>
This application allows to explore waterlevels and precipitation data using various visualisation techniques. It also allows to generate and download
various pdf-reports. 

### More Information
- [MOE Metadata](https://files.ontario.ca/moe_mapping/downloads/metadata/opendata/pgmn_metadata.pdf)
- [Metadata record](https://data.ontario.ca/dataset/provincial-groundwater-monitoring-network/resource/2f97f6cf-9b2d-4dd7-8c41-64f51f1773b9)
- [Conservation Ontario](https://conservationontario.ca/)
"""

class App():
    def __init__(self, df_stations, df_waterlevels, df_precipitation, df_wl_stations, df_precipitation_stations):
        self.df_stations = df_stations
        self.df_waterlevels = df_waterlevels
        self.df_precipitation = df_precipitation
        self.df_wl_stations = df_wl_stations
        self.df_precipitation_stations = df_precipitation_stations
    
    def show_menu(self):
        st.markdown(f'## Ontario Provincial Groundwater Monitoring Network (PGMN)')
        st.markdown( text.format(len(self.df_stations), len(self.df_wl_stations), len(self.df_precipitation_stations)), unsafe_allow_html=True ) 

    

