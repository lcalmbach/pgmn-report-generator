from __future__ import print_function
import pandas as pd
import numpy as np
import os
import glob
# import streamlit as st
from datetime import date, timedelta

BASE_DATA = os.path.join(os.getcwd(), 'static','data')
BASE_PRECIPITATION = os.path.join(os.getcwd(), 'static','data', 'precipitation')
PRECIPITATION_FILE = os.path.join(os.getcwd(), 'static','data', 'daily_prec.csv')
WL_FILE = os.path.join(os.getcwd(), 'static','data', 'daily_wl.csv')
BASE_WATER_LEVELS = os.path.join(os.getcwd(), 'static','data', 'water_levels')
CSS_STYLE_FILE = './style.css'
STATION_FILE = os.path.join(BASE_DATA, 'PGMN_WELLS_NAD83.csv') 
MISSING_VALUE = -99

def generate_missing_data_rows(df):
    min_date = df['date'].min()
    max_date = df['date'].max()
    well = df['CASING_ID'][0]
    data = pd.date_range(start=min_date, end=max_date)
    df_all_dates = pd.DataFrame({'date': data})
    missing_data_df = pd.merge(df_all_dates, df, on='date', how='left')
    missing_data_df = missing_data_df[missing_data_df['CASING_ID'].isna()]
    
    old_date = min_date - timedelta(10)
    for date in missing_data_df['date']:
        if (date - old_date).days > 1:
            record = {'CASING_ID': well, 'date': date, 'wl_elev': MISSING_VALUE}
            df = df.append(record,ignore_index=True)
        old_date = date
    
    return df

def convert_wl_data():
    df_wl = pd.DataFrame()
    rows = 0
    
    file_list = glob.glob(f"{BASE_WATER_LEVELS}/*.zip")
    for f in file_list:
        try:
            df = pd.read_csv(f, sep=",")            
            df = df.rename(columns={'Water_Level_Elevation_meter_above_sea_level': 'wl_elev'})
            df['date'] = pd.to_datetime(df['READING_DTTM']).dt.date    
            df['date'] = pd.to_datetime(df['date'])   
            rows += len(df)
            df = df.groupby(['CASING_ID', 'date']).agg('mean').reset_index()            
            # days with no water level measurements are not recorded. they need a wl_elev = NAN record
            # in order for Altair to leave a gap between points having missing datapoints between them 
            df = generate_missing_data_rows(df)
            df_wl = df_wl.append(df)
            print(f)
        except Exception as ex:
            print(f'error in {f}:{ex}')
    
    fields = ['CASING_ID', 'date', 'wl_elev']
    df_wl['wl_elev'] = df_wl['wl_elev'].apply('{:.2f}'.format)
    # convert missing value back to NAN, if I set it initially to NAN then the format does not work and 
    # requires conditional formatting in the line above, which I have not figured out. 
    df_wl['wl_elev'] = df_wl['wl_elev'].replace('{:.2f}'.format(MISSING_VALUE), np.NAN)
    df_wl[fields].to_csv(WL_FILE, sep=';', index=False)    

def convert_precipitation_data():
    rows = 0
    df_prec = pd.DataFrame()
    file_list = glob.glob(f"{BASE_PRECIPITATION}/*.csv")
    for f in file_list:
        try:
            df = pd.read_csv(f, sep=",", dtype={'DataRecordMetaID': pd.np.integer,'LocationWell': object,'READING_DTTM': object,'AccumulationFinal': pd.np.float64,'ReadingStatus': object,'Reason': object})
            df = df[(df['ReadingStatus']=='Acceptable') & (df['AccumulationFinal'] > 0)]
            df['READING_DTTM'] = pd.to_datetime(df['READING_DTTM'])    
            df['date'] = df['READING_DTTM'].dt.date 
            df = df.groupby(['LocationWell','date']).agg('sum').reset_index()
            df_prec = df_prec.append(df)
            print(f)
        except Exception as ex:
            print(f'error in {f}:{ex}')
    
    df_prec['date'] = pd.to_datetime(df_prec['date'])
    df_prec['location_id'] = df_prec.apply(lambda row: int(row['LocationWell']) if row['LocationWell'].find('-') == -1 else int(row['LocationWell'][0:row['LocationWell'].find('-')]) , axis=1)   

    print('saving file with all stations')
    fields = ['LocationWell','location_id','date','AccumulationFinal']
    df_prec[fields].to_csv(PRECIPITATION_FILE, sep=';', index=False)
    print('done')

if __name__ == "__main__":
    convert_wl_data()
    #convert_precipitation_data()

