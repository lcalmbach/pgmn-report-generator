from __future__ import print_function
import pandas as pd
import streamlit as st
import jinja2
import pdfkit
import base64
import os
import sys
import subprocess
import platform
import plotly.express as px
import numpy as np
import glob
import calendar

from streamlit.type_util import _PANDAS_INDEX_TYPE_STR

TABLE_TEMPLATE_FILE = "table_template.html"
FIG_TEMPLATE_FILE = "figure_template.html"
BASE_HTML = os.path.join(os.getcwd(), 'html')
BASE_FIG = os.path.join(os.getcwd(), 'images')
PDF_TARGET_FILE = f"./pdf/output.pdf"
CSS_STYLE_FILE = './style.css'
WKHTMLTOPDF_PATH = 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
user_settings = {}

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_data(path: str, sep_char: str):
    data_frames = {}
    rows = 0
    ok = False
    info = st.empty()
    try:
        file_list = glob.glob(f"{path}*.zip")
        for f in file_list:
            info.write(f"reading file {f}")
            df = pd.read_csv(f, sep=sep_char)
            df = df.rename(columns={'READING_DTTM':'date', 'Water_Level_Elevation_meter_above_sea_level': 'wl_elev'})
            df['date'] = pd.to_datetime(df['date'])            
            rows += len(df)
            station = df.iloc[0]['CASING_ID']
            data_frames[station] = df
        ok = True
        st.info(f"Success: {len(file_list)} files read, {rows} rows")
    except Exception as ex:
        print(ex)
    finally:
        return data_frames, True
    

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href


def get_base64_encoded_image(image_path):
    """
    returns bytecode for an image file
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def create_html_files(data_frames):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "report_template.html"
    template = templateEnv.get_template(TEMPLATE_FILE)
    for d in data_frames:
        outputText = template.render(df=d['df'],
                interest_rate=d['interest_rate'])
        file_name = r'C:\Users\lcalm\OneDrive\dev\pdf-generator\html\\' + str(int(d['interest_rate'] * 100)) + '.html'
        html_file = open(file_name, 'w')
        html_file.write(outputText)
        html_file.close()
    
    TEMPLATE_FILE = "image_template.html"
    template = templateEnv.get_template(TEMPLATE_FILE)
    bytes = get_base64_encoded_image(r'C:\Users\lcalm\OneDrive\dev\pdf-generator\images\fig1.png')
    description = "this is a description this is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a descriptionthis is a description"
    outputText = template.render(bytes=bytes,description=description)
    html_file = open(r'C:\Users\lcalm\OneDrive\dev\pdf-generator\html\\' + 'img.html', 'w')
    html_file.write(outputText)
    html_file.close()


def plot_time_series(df, year):    
    fig = px.line(df, x="date", y=df['wl_elev'],
              hover_data={"date": "|%B %d, %Y"})
    fig.update_xaxes(tickformat="%b\n%Y", title = None, range = (f'{year}-01-01', f'{year+1}-01-01'))
    fig.update_yaxes(title="Water level elevation(masl)")
    return fig
    

def get_file_name(station, year, fmt):
    if fmt in ('png','jpeg'):
        path = './images/'
    else:
        path = './html/'
    return f"{path}{station}_{year}.{fmt}"


def save_plot(fig, station, year):
    file_name = f"./images/{station}_{year}.png"
    fig.write_image(file_name, engine="kaleido")


def get_monthly_stat_df(df):
    df_stat = df[['month', 'wl_elev']].groupby(['month']).agg(['min', 'max', 'mean', 'std'])
    df_stat = df_stat.reset_index()
    df_stat['month'] = df_stat['month'].apply(lambda x: calendar.month_abbr[x])
    return df_stat


def create_html_table(df, station, year):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    
    template = templateEnv.get_template(TABLE_TEMPLATE_FILE)
    outputText = template.render(df=df, station=station)
    file_name = f'tab-{station}-{year}.html'
    file_name = os.path.join(BASE_HTML, f'tab-{station}-{year}.html')
    html_file = open(file_name, 'w')
    html_file.write(outputText)
    html_file.close()


def create_html_fig(station,year):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(FIG_TEMPLATE_FILE)
    # find the saved file and encode it
    file_name = get_file_name(station,year,'png')
    bytes = get_base64_encoded_image(file_name)
    outputText = template.render(bytes=bytes)

    file_name = os.path.join(BASE_HTML, f'fig-{station}-{year}.html')
    html_file = open(file_name, 'w')
    html_file.write(outputText)
    html_file.close()


def generate_report(report_type, data_frames, stations, year):
    def _create_html_file():
        for station in stations:
            df = data_frames[station]
            if report_type.lower() == 'monthly':
                df['year'] = pd.DatetimeIndex(df['date']).year 
                #  filter for required year
                df_filtered = df[df['year'] == year].copy()
                df_filtered['month'] = pd.DatetimeIndex(df_filtered['date']).month
                df_stat = get_monthly_stat_df(df_filtered)
                if len(df_filtered) > 0:
                    fig = plot_time_series(df_filtered, year)
                    save_plot(fig, station, year)
                    create_html_table(df_stat, station, year)
                    create_html_fig(station,year)
                else:
                    st.write(f'no data availale for this station in {year}')
            else:
                df['year'] = pd.DatetimeIndex(df['date']).year
        
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
            'header-center': user_settings['report_title'],
            'print-media-type': None
            }
        source_code = ''
        for station in stations:
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

    st.info('creating html file')
    _create_html_file()
    st.info('generating pdf file')
    _create_pdf_files()
    st.success('Done')
    
    base64_pdf = get_base64_encoded_image(PDF_TARGET_FILE)
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">' 
    st.markdown(pdf_display, unsafe_allow_html=True)
    st.markdown(get_binary_file_downloader_html(PDF_TARGET_FILE), unsafe_allow_html=True)


def preview_report(rep_type, data_frames, stations,  year):    
    for station in stations:
        df = data_frames[station]
        if rep_type.lower() == 'monthly':
            df['year'] = pd.DatetimeIndex(df['date']).year 
            #  filter for required year
            df_filtered = df[df['year'] == year].copy()
            df_filtered['month'] = pd.DatetimeIndex(df_filtered['date']).month
            df_stat = get_monthly_stat_df(df_filtered)
            st.markdown(f'<div style="text-align:center"><b>{station}</b></div>', unsafe_allow_html=True)
            if len(df_filtered) > 0:
                fig = plot_time_series(df_filtered, year)
                st.write(fig)
                save_plot(fig, station, year)
                st.write(df_stat)
            else:
                st.write(f'no data availale for this station in {year}')
        else:
            df['year'] = pd.DatetimeIndex(df['date']).year
    

def main():
    global user_settings
    st.sidebar.markdown("### 🌍 PGMN water levels")
    data_folder = "./test_data/"
    data_frames, ok = get_data(data_folder, ",")
    if ok:     
        all_stations = st.sidebar.checkbox('All stations')
        if all_stations:
            default = list(data_frames.keys())
            stations = st.sidebar.multiselect("Station", list(data_frames.keys()), default)
        else:
            lst = list(data_frames.keys())
            default = [lst[0]]
            stations = st.sidebar.multiselect("Station", list(data_frames.keys()), default)
        report_type = st.sidebar.selectbox("Report type",['Monthly','Yearly'])
        if report_type == 'Monthly':
            year = st.sidebar.selectbox("Year", range(2001,2021))
        
        # report settings
        user_settings['report_title'] = f"PGMN water levels - {year}"
        
        col1, col2 = st.sidebar.beta_columns((1,2.8))
        if col1.button("Preview"):
            preview_report(report_type, data_frames, stations, year)
        if col2.button("Generate Report"):            
            generate_report(report_type, data_frames, stations, year)            


if __name__ == "__main__":
    main()

