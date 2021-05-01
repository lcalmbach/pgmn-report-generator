from __future__ import print_function
import pandas as pd
import streamlit as st
import altair as alt
import tools

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

        def get_stations():
            df =  self.df_station
            if self.settings['cons_authorities'] != []:
                filter = df['CONS_AUTHO'].isin(self.settings['cons_authorities']) 
                df =  self.df_station[filter]
            
            if self.settings['aquifer_types'] != []:
                filter = df['AQUIFER_TY'].isin(self.settings['aquifer_types'])
                df =  df[filter]

            return list(df['PGMN_WELL'])

        def show_plot():            
            figs = []
            dfs = []
            config={}
            for station in self.settings['stations']:
                if self.settings['avg_days']:
                    df = self.data_frames[station].copy()
                    df['date'] = df['date'].dt.date 
                    df = df.groupby(['CASING_ID', 'date']).agg('mean').reset_index()
                    df['date'] = pd.to_datetime(df['date'])    
                else:
                    df = self.data_frames[station] 
                if self.settings['group_by_year']:
                    for year in range(self.settings['year_from'], self.settings['year_to']):                            
                        dfs.append(df[df['year'] == year])
                        if len(dfs[-1])>0:
                            title = f'{station} ({year})'

                            figs.append(self.plot_time_series(dfs[-1],config))
                            st.write(figs[-1]) 
                elif len(df)>0:
                    df = df[ (df['year']>= self.settings['year_from']) & (df['year']<= self.settings['year_to']) ]
                    config['title'] = f"{station} ({self.settings['year_from']} - {self.settings['year_to']})"
                    config['width'] =  self.settings['width']
                    config['height'] = self.settings['height']
                    config['rolling_avg_int'] = self.settings['rolling_avg_int']
                    fig = self.plot_time_series(df, config)
                    st.write(fig)

        def show_filter():
            default=[self.lst_conservation_authorities[0]]
            self.settings['cons_authorities'] = st.sidebar.multiselect("Conservation authority", self.lst_conservation_authorities, [])
            default=[self.lst_aquifer[0]]
            self.settings['aquifer_types'] = st.sidebar.multiselect("Aquifer types", self.lst_aquifer, [])
            self.stations = get_stations()
            default = [self.stations[0]]
            self.settings['stations'] = st.sidebar.multiselect("Station", self.stations, default)
            self.settings['year_from'], self.settings['year_to'] = st.sidebar.select_slider("Years", range(2001,2020),[2001,2002])
            self.settings['group_by_year'] = st.sidebar.checkbox("Group plots by year")
            self.settings['avg_days'] = st.sidebar.checkbox("Plot daily average values")
            self.settings['width'] = st.sidebar.number_input('Plot width (px)', value=800,min_value=100,max_value=10000)
            self.settings['height']= st.sidebar.number_input('Plot height (px)', value=300,min_value=100,max_value=10000)
            self.settings['rolling_avg_int']= st.sidebar.number_input('Rolling average interval', value=0,min_value=0,max_value=100000)
        
        show_filter()
        show_plot()

    def plot_time_series(self, df, config):
        min = df['wl_elev'].min()
        max = df['wl_elev'].max()
        min_year = int(df['year'].min())
        max_year = int(df['year'].max() + 1)

        min = tools.truncate(min, 0) 
        max = tools.truncate(max + 1, 0) 

        raw_data = alt.Chart(df).mark_line().encode(
            alt.X('date:T',
                scale = alt.Scale(domain=(f'01-01-{min_year}', f'01-01-{max_year}')),
                axis=alt.Axis(title=""),
            ),
            alt.Y('wl_elev:Q', 
                scale = alt.Scale(domain=(min,max)),
                axis=alt.Axis(title="water level (masl)"),
            ),
            tooltip=['CASING_ID', 'date', 'wl_elev']
        )
        if config['rolling_avg_int'] > 0:
            rolling_avg = alt.Chart(df).mark_line(
                    color='red',
                    size=2
                ).transform_window(
                    rolling_mean='mean(wl_elev)',
                    frame=[-config['rolling_avg_int'] / 2, config['rolling_avg_int'] / 2],
            ).encode(
                x='date:T',
                y='rolling_mean:Q'
            )
        if config['rolling_avg_int'] > 0:
            fig = (raw_data + rolling_avg)
        else:
            fig = raw_data
        fig = fig.properties(
            title=config['title'],
            width=config['width'],
            height=config['height']
        )
        return fig
    

