from __future__ import print_function
import pandas as pd
import streamlit as st
import jinja2
import pdfkit
import os
import sys
import subprocess
import platform
import plotly.express as px
import numpy as np
import tools
import calendar

TABLE_TEMPLATE_FILE = "table_template.html"
FIG_TEMPLATE_FILE = "figure_template.html"
BASE_HTML = os.path.join(os.getcwd(), 'html')
BASE_PDF = os.path.join(os.getcwd(), 'pdf')
BASE_FIG = os.path.join(os.getcwd(), 'images')
BASE_DATA = os.path.join(os.getcwd(), 'test_data')
PDF_TARGET_FILE = os.path.join(BASE_PDF, 'test_data') #f"./pdf/output.pdf"
CSS_STYLE_FILE = './style.css'
WKHTMLTOPDF_PATH = 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
STATION_FILE = os.path.join(BASE_DATA, 'PGMN_WELLS_NAD83.csv') #'./test_data/PGMN_WELLS_NAD83.csv'
user_settings = {}


class App:
    def __init__(self, data_frames, df_station):
        self.data_frames = data_frames
        self.df_station = df_station
        self.settings = {}
        self.lst_conservation_authorities = list(df_station['CONS_AUTHO'])
        self.lst_aquifer = list(df_station['AQUIFER_TY'])

    
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

        def show_filter():
            default=[self.lst_conservation_authorities[0]]
            self.settings['cons_authorities'] = st.sidebar.multiselect("Conservation authority", self.lst_conservation_authorities, [])
            default=[self.lst_aquifer[0]]
            self.settings['aquifer_types'] = st.sidebar.multiselect("Aquifer types", self.lst_aquifer, [])
            self.stations = get_stations()
            default = [self.stations[0]]
            self.settings['stations'] = st.sidebar.multiselect("Station", self.stations, default)
            self.settings['year_from'], self.settings['year_to'] = st.sidebar.select_slider("Years", range(2001,2020),[2001,2002])
            self.settings['report_title'] = st.sidebar.text_input('Report title')
            
        show_filter()
        self.generate_report(self.data_frames, self.settings['stations'], range(self.settings['year_from'], self.settings['year_to'] + 1))            



    def plot_time_series(self,df, year):    
        fig = px.line(df, x="date", y=df['wl_elev'],
                hover_data={"date": "|%B %d, %Y"})
        fig.update_xaxes(tickformat="%b\n%Y", title = None, range = (f'{year}-01-01', f'{year+1}-01-01'))
        fig.update_yaxes(title="Water level elevation(masl)")
        return fig
    

    def get_file_name(self,station, year, fmt):
        if fmt in ('png','jpeg'):
            path = './images/'
        else:
            path = './html/'
        return f"{path}{station}_{year}.{fmt}"


    def save_plot(self,fig, station, year):
        file_name = f"./images/{station}_{year}.png"
        fig.write_image(file_name, engine="kaleido")


    def get_monthly_stat_df(self,df):
        df_stat = df[['month', 'wl_elev']].groupby(['month']).agg(['min', 'max', 'mean', 'std'])
        df_stat = df_stat.reset_index()
        df_stat['month'] = df_stat['month'].apply(lambda x: calendar.month_abbr[x])
        return df_stat


    def create_html_table(self, df, station, year):
        templateLoader = jinja2.FileSystemLoader(searchpath="./")
        templateEnv = jinja2.Environment(loader=templateLoader)
        
        template = templateEnv.get_template(TABLE_TEMPLATE_FILE)
        outputText = template.render(df=df, station=f"{station} ({year})")
        file_name = f'tab-{station}-{year}.html'
        file_name = os.path.join(BASE_HTML, f'tab-{station}-{year}.html')
        html_file = open(file_name, 'w')
        html_file.write(outputText)
        html_file.close()


    def create_html_fig(self, station,year):
        templateLoader = jinja2.FileSystemLoader(searchpath="./")
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(FIG_TEMPLATE_FILE)
        # find the saved file and encode it
        file_name = self.get_file_name(station,year,'png')
        bytes = tools.get_base64_encoded_image(file_name)
        outputText = template.render(bytes=bytes)

        file_name = os.path.join(BASE_HTML, f'fig-{station}-{year}.html')
        html_file = open(file_name, 'w')
        html_file.write(outputText)
        html_file.close()


    def generate_report(self, data_frames, stations, years):
        def _create_html_file():
            for station in stations:
                for year in years:
                    df = data_frames[station]
                    df['year'] = pd.DatetimeIndex(df['date']).year 
                    #  filter for required year
                    df_filtered = df[df['year'] == year].copy()
                    df_filtered['month'] = pd.DatetimeIndex(df_filtered['date']).month
                    df_stat = self.get_monthly_stat_df(df_filtered)
                    if len(df_filtered) > 0:
                        fig = self.plot_time_series(df_filtered, year)
                        self.save_plot(fig, station, year)
                        self.create_html_table(df_stat, station, year)
                        self.create_html_fig(station,year)
                    else:
                        st.write(f'no data availale for this station in {year}')
            
        def _create_pdf_files():
            """
            all options, see: https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
            """
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'custom-header' : [
                    ('Accept-Encoding', 'gzip')
                ],
                'no-outline': None,
                'footer-right': '[page]/[topage]',
                'footer-line': None,
                'footer-left': '[isodate]',
                'footer-spacing': '10.0', 
                'header-spacing': '10.0', 
                'header-line': None, 
                'header-center': self.settings['report_title'],
                'print-media-type': None
                }
            source_code = ''
            for station in stations:
                for year in years:
                    file_name = os.path.join(BASE_HTML, f'tab-{station}-{year}.html')
                    if os.path.isfile(file_name):         
                        #read html code to string
                        html_file = open(file_name, 'r', encoding='utf-8')
                        source_code += html_file.read() 
                        # same for figure
                        file_name = os.path.join(BASE_HTML, f'fig-{station}-{year}.html')
                        html_file = open(os.path.join(BASE_HTML, file_name), 'r', encoding='utf-8')
                        source_code += '<br><br>' + html_file.read() 
                        # write the page break
                        source_code += '<p class="new-page"></p>'
                    else:
                        st.write(f'{file_name} not found')
                
            if platform.system() == "Windows":
                pdfkit_config = pdfkit.configuration(wkhtmltopdf=os.environ.get('WKHTMLTOPDF_BINARY', WKHTMLTOPDF_PATH))
            else:
                os.environ['PATH'] += os.pathsep + os.path.dirname(sys.executable) 
                WKHTMLTOPDF_CMD = subprocess.Popen(['which', os.environ.get('WKHTMLTOPDF_BINARY', 'wkhtmltopdf-pack')], 
                    stdout=subprocess.PIPE).communicate()[0].strip()
                pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)    
            
            pdfkit.from_string(source_code, PDF_TARGET_FILE, configuration=pdfkit_config, css=CSS_STYLE_FILE, options=options)

        if st.button("Create pdf report"):
            st.info('creating html file')
            _create_html_file()
            st.info('generating pdf file')
            _create_pdf_files()
            st.success('Done')
        
        base64_pdf = tools.get_base64_encoded_image(PDF_TARGET_FILE)
        pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">' 
        st.markdown(pdf_display, unsafe_allow_html=True)
        st.markdown(tools.get_binary_file_downloader_html(PDF_TARGET_FILE), unsafe_allow_html=True)
    

