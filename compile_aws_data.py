# -*- coding: utf-8 -*-
"""
@author: bav@geus.dk

tip list:
    %matplotlib inline
    %matplotlib qt
    import pdb; pdb.set_trace()
"""
import xarray as xr
import pandas as pd 
import numpy as np
import nead
import os

path_l3 = 'C:/Users/bav/GitHub/PROMICE data/aws-l3-dev/level_3/'
fig_folder = 'figures/CARRA_vs_AWS/'

variables = ['time','stid','t_u', 'rh_u','rh_u_cor', 'qh_u','p_u', 'wspd_u','dlr', 'ulr', 
            't_surf',  'albedo', 'dsr', 'dsr_cor',  'usr',  'usr_cor','dlhf_u','dshf_u']
df_aws_all = pd.DataFrame()

freq = 'H'
# %% loading PROMICE stations
print('loading PROMICE')
df_meta_promice = pd.read_csv(path_l3+'../AWS_metadata.csv')
df_meta_promice = df_meta_promice.loc[df_meta_promice.location_type == 'ice sheet']
df_meta_promice['source'] ='PROMICE/GC-Net'

for station in df_meta_promice.stid:    
    if freq == 'D':
        df_aws = pd.read_csv(path_l3 + station + '/'+station+'_day.csv')
    elif freq == 'H':
        df_aws = pd.read_csv(path_l3 + station + '/'+station+'_hour.csv')
    df_aws.time = pd.to_datetime(df_aws.time, utc=True)
    df_aws=df_aws.set_index('time')   
    df_aws['stid'] = station        
    # for v in variables:
    #     if v not in df_aws.columns:
    #         df_aws[v] = np.nan
    df_aws['stid'] = station
    df_aws.index = pd.to_datetime(df_aws.index,utc=True,format='mixed')
    df_aws = df_aws[[v for v in variables if v in df_aws.columns]]
    df_aws_all = pd.concat((df_aws_all, df_aws.reset_index()), ignore_index=True)

# %% GC-Net stations
print('loading GC-Net historical')
if os.path.isdir('C:/Users/bav/OneDrive - GEUS/Code/'):
    base_path = 'C:/Users/bav/OneDrive - GEUS/Code/'
else:
    base_path = 'C:/Users/bav/OneDrive - Geological survey of Denmark and Greenland/Code/'
    
path_to_gcnet = base_path + '/PROMICE/GC-Net-Level-1-data-processing/L1/'
df_meta_gcnet = pd.read_csv(path_to_gcnet+'GC-Net_location.csv', skipinitialspace=True)

df_meta_gcnet['source'] = 'GC-Net historical'
df_meta_gcnet = df_meta_gcnet.loc[df_meta_gcnet['Latitude (°N)']>0, 
                        ['Name','Latitude (°N)', 'Longitude (°E)', 'Elevation (wgs84 m)','source']
                        ].rename(columns={'Name':'stid',
                              'Latitude (°N)':'lat_installation',
                              'Longitude (°E)':'lon_installation',
                              'Elevation (wgs84 m)':'alt_installation'})
                                          
for station in df_meta_gcnet.stid:
    df_aws = nead.read(path_to_gcnet+'daily/'+station.replace(' ','')+'_daily.csv').to_dataframe()

    if freq == 'D':
        df_aws = nead.read(path_to_gcnet+'daily/'+station.replace(' ','')+'_daily.csv').to_dataframe()
    elif freq == 'H':
        df_aws = nead.read(path_to_gcnet+'hourly/'+station.replace(' ','')+'.csv').to_dataframe()
        
    df_aws['time'] = pd.to_datetime(df_aws.timestamp)
    df_aws = df_aws.set_index('time')
    
    for v in ['VW1','VW2','RH1','RH2','RH1_cor','RH2_cor','TA1','TA2','TA3','TA4','Q1','Q2']:
        if v not in df_aws.columns:
            df_aws[v] = np.nan
    df_aws['VW2'] = df_aws['VW2'].combine_first(df_aws['VW1'])
    df_aws['RH2'] = df_aws['RH2'].combine_first(df_aws['RH1'])
    df_aws['RH2_cor'] = df_aws['RH2_cor'].combine_first(df_aws['RH1_cor'])
    df_aws['Q2'] = df_aws['Q2'].combine_first(df_aws['Q1'])
    df_aws['TA2'] = (df_aws['TA2']
                     .combine_first(df_aws['TA1'])
                     .combine_first(df_aws['TA3'])
                     .combine_first(df_aws['TA4']))
    df_aws = df_aws.rename(columns={
                'ISWR':'dsr',  'OSWR':'usr', 
                'RH2':'rh_u','RH2_cor':'rh_u_cor', 'TA2':'t_u',
                'VW2':'wspd_u','P':'p_u','LHF':'dlhf_u',
                'Alb':'albedo','Q2':'qh_u','SHF':'dshf_u'
                                    })

    df_aws = df_aws[[v for v in variables if v in df_aws.columns]]            
    # for v in variables:
    #     if v not in df_aws.columns:
    #         df_aws[v] = np.nan
    df_aws['stid'] = station
    # df_aws['program'] = 'PROMICE/GC-Net'
    # df_aws['institute'] = 'GEUS, Copenhagen, Denmark'
    df_aws.index = pd.to_datetime(df_aws.index,utc=True,format='mixed')
    df_aws = df_aws[[v for v in variables if v in df_aws.columns]]
    df_aws_all = pd.concat((df_aws_all,df_aws.reset_index()), ignore_index=True)


# %% import SIGMA data
print('load SIGMA-A station')
df_sigma = pd.read_csv(base_path+'/AWS/SIGMA/SIGMA-A/DATA/SIGMA_AWS_SiteA_2012-2020_Lv1_3.csv')
df_sigma.dropna(axis=1, how='all', inplace=True)
df_sigma.rename(columns={
    'date': 'time', 'U1': 'wspd_u', 'WD1': 'wdir_u', 'T1': 't_u',
    'RH1': 'rh_u', 'U2': 'wspd_l', 'WD2': 'wdir_l', 'T2': 't_l',
    'RH2': 'rh_l', 'SWd': 'dsr', 'SWu': 'usr', 'LWd': 'dlr',
    'LWu': 'ulr',  'Pa': 'p_u',
    'sensor_height1': 'z_boom_l',
    'sensor_height2': 'z_boom_u',
    'Ts':'t_surf'
}, inplace=True)
for v in df_sigma.columns:
    if v != 'time':
        df_sigma.loc[df_sigma[v]<-2000, v] = np.nan

df_sigma['time'] = pd.to_datetime(df_sigma.time, utc=True)
df_sigma = df_sigma.set_index('time')
if freq == 'D':
    df_sigma=df_sigma.resample('D').mean()

df_sigma['stid'] = 'SIGMA-A'
df_sigma = df_sigma[[v for v in variables if v in df_sigma.columns]]

df_aws_all = pd.concat((df_aws_all,df_sigma.reset_index()), ignore_index=True)

# %% Mejia (not yet extracted from CARRA)
# df_high = pd.read_csv(base_path+'/AWS/Mejia/HIGH_WEA_2017_2018.csv')
# df_high.rename(columsn={'Date Time, GMT+00:00':'time',
#                         'wind_speed':'wspd_u', 'air_temp':'t_u',
#         'relative_humidity':'rh_u', 'reflected_solar_radiation':'usr',
#         'incoming_solar_radiation':'dsr', 
#         'incoming_solar_radiation_corrected':'dsr_cor'})
# df_lowc = pd.read_csv(base_path+'/AWS/Mejia/LOWC_WEA_2017_2018.csv')
# 69.4727N, 49.8263W), elevation: ~780 
# HIGH weather station data. (69.5416N, 49.7100W). Elevation: ~950 m asl

# %% IMAU
print('load IMAU stations')
list_df = []
for st in ['S5','S6','S9','S10']:
    for yr in range(2003,2023):
        file = base_path+'/AWS/IMAU K-transect/datasets/K-transect_AW'+st+'_'+str(yr)+'.tab'
        if os.path.isfile(file):
            skip_header = 0
            with open(file, 'r') as f:
                for i, line in enumerate(f):
                    skip_header = i + 1
                    if line.startswith('*/'):
                        break
            tmp  = pd.read_csv(file,sep='\t',skiprows=skip_header).rename(columns={'Date/Time':'time', 
                 'dd [deg]':'wdir_u', 'ff [m/s]':'wspd_u', 'SWD [W/m**2]':'dsr',
                 'SWU [W/m**2]':'usr', 'LWD [W/m**2]':'dlr', 'LWU [W/m**2]':'ulr',
                 'T body [°C]':'t_rad', 'TTT [°C]':'t_u', 'RH [%]':'rh_u',
                   'PPPP [hPa]':'p_u', 'Height rel [m]':'sh'})
            tmp['time'] = pd.to_datetime(tmp.time, utc=True, format='mixed')
            if freq == 'D':
                tmp = tmp.set_index('time').resample('D').mean().reset_index()
            
            tmp['stid'] = st.lower()
            list_df.append(tmp)
        
df_imau = pd.concat(list_df)
df_imau = df_imau[[v for v in variables if v in df_imau.columns]]

df_aws_all = pd.concat((df_aws_all, df_imau.reset_index()), ignore_index=True)

# %% FA
print('load FA stations')
df = pd.read_csv(base_path+'AWS/Firn Aquifer/SE_GRN_SEB_1416_hr_small.txt', delim_whitespace=True)
df['time'] = df['year'].astype(str) + ' ' + df['day'].astype(str) + ' ' + df['hour'].astype(str)
df['time'] = pd.to_datetime(df['time'], format='%Y %j %H.%M',utc=True)
df.drop(['year', 'day', 'hour'], axis=1, inplace=True)

df = df.rename(columns={'Tair_2m':'t_u', 'qair_2m':'qh_u', 'pres':'p_u', 
                        'FF_10m':'wspd_u', 'WD':'wdir_u', 'SWin':'dsr',
                        'SWout':'usr', 'LWin':'dlr'})
df=df.set_index('time')
if freq == 'D':
    df = df.resample('D').mean()
df['stid'] = 'FA-13'
df.loc['2015-07-01':,'stid']='FA15-1'
# FA-13
# Latitude: 66.1812° N
# Longitude: 39.0435° W
# Elevation: 1563 meters (ellipsoid height WGS84)
# FA-15-1,,66.3622,-39.3119,1664
# FA-15-2,,66.3548,-39.1788,1543
df = df[[v for v in variables if v in df.columns]]

df_aws_all = pd.concat((df_aws_all, df.reset_index()), ignore_index=True)

# %% Covi
print('load Covi stations')
if freq == 'D':
    tag = 'daily'
    fl = ['AWS_EKT_20170507_20190904_'+tag+'.txt','AWS_SiteJ_20170429_20190904_'+tag+'.txt']
else:
    tag = 'hourly'
    fl = ['AWS_EKT_20170506_20190905_'+tag+'.txt','AWS_SiteJ_20170428_20190905_'+tag+'.txt']
for f in fl:
    df = pd.read_csv(base_path+'AWS/Covi/data/'+f, skiprows=1)
    df = df.rename(columns={'TIMESTAMP(WGT)':'time', 'Tair(C)':'t_u',
            'RH(%)':'rh_u', 'SWin(W/m2)':'dsr', 'SWout(W/m2)':'usr', 'LWin(W/m2)':'dlr',
            'LWout(W/m2)':'ulr', 'Wspd(m/s)':'wspd_u','Wdir(deg)':'wdir_u'})
    df['time'] = pd.to_datetime(df.time,utc=True)
    # df = df.resample('D').mean()
    df['stid'] = f.split('_')[1]
    if f.split('_')[1] == 'SiteJ':
        df['stid'] = 'Site J'
        
    df = df[[v for v in variables if v in df.columns]]
    df_aws_all = pd.concat((df_aws_all, df), ignore_index=True)

# %% export to netcdf
df_aws_all.time = df_aws_all.time.dt.tz_localize(None)
df_aws_all = df_aws_all.set_index(['time','stid'])
ds_aws_all = df_aws_all.to_xarray()
# adding 
df_meta = pd.read_csv('data/AWS_station_locations.csv').set_index('stid')
df_meta = df_meta[['lat','lon','alt']]#.rename(columns={'lat':'latitude','lon':'longitude','alt':'elevation'})
ds_aws_all = xr.merge((ds_aws_all, df_meta.to_xarray()),compat='override')
comp = dict(zlib=True, complevel=5)
encoding = {var: comp for var in ds_aws_all.data_vars}
ds_aws_all.to_netcdf('data/AWS_compilation_'+tag+'.nc', encoding=encoding)

# %% overview table
table = xr.Dataset()
for station in ds_aws_all.stid:
    table= xr.merge((table, xr.merge((
        ds_aws_all.where(ds_aws_all.stid==station, drop=True)[
            ['lat','lon','alt']],
        ds_aws_all.where(ds_aws_all.stid==station, drop=True)[
            ['t_u']].dropna(dim='time').count(dim='time')))))

table.to_dataframe().to_csv('data/AWS_compilation_overview_'+tag+'.csv')
    