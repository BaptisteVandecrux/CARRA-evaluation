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

path_l3 = 'C:/Users/bav/GitHub/PROMICE data/aws-l3-dev/level_3/'
fig_folder = 'figures/CARRA_vs_AWS/'

variables = ['t_u', 'rh_u','rh_u_cor', 'qh_u','p_u', 'wspd_u','dlr', 'ulr', 
            't_surf',  'albedo', 'dsr', 'dsr_cor',  'usr',  'usr_cor','dlhf_u','dshf_u']
df_aws_all = pd.DataFrame()

# %% loading PROMICE stations
df_meta_promice = pd.read_csv(path_l3+'../AWS_metadata.csv')
df_meta_promice = df_meta_promice.loc[df_meta_promice.location_type == 'ice sheet']
df_meta_promice['source'] ='PROMICE/GC-Net'

for station in df_meta_promice.stid:    
    df_aws = pd.read_csv(path_l3 + station + '/'+station+'_day.csv')[['time']+variables]
    df_aws.time = pd.to_datetime(df_aws.time, utc=True)
    df_aws=df_aws.set_index('time')   
    df_aws['stid'] = station        
    for v in variables:
        if v not in df_aws.columns:
            df_aws[v] = np.nan
    df_aws['stid'] = station
    df_aws.index = pd.to_datetime(df_aws.index,utc=True)
    
    df_aws_all = pd.concat((df_aws_all,df_aws))

# %% GC-Net stations
try:
    path_to_gcnet = 'C:/Users/bav/OneDrive - GEUS/Code/PROMICE/GC-Net-Level-1-data-processing/L1/'
    df_meta_gcnet = pd.read_csv(path_to_gcnet+'GC-Net_location.csv', skipinitialspace=True)
except:
    path_to_gcnet = 'C:/Users/bav/OneDrive - Geological Survey of Denmark and Greenland/Code/PROMICE/GC-Net-Level-1-data-processing/L1/'
    df_meta_gcnet = pd.read_csv(path_to_gcnet+'GC-Net_location.csv', skipinitialspace=True)
    
df_meta_gcnet['source'] = 'GC-Net historical'
df_meta_gcnet = df_meta_gcnet.loc[df_meta_gcnet['Latitude (°N)']>0, 
                        ['Name','Latitude (°N)', 'Longitude (°E)', 'Elevation (wgs84 m)','source']
                        ].rename(columns={'Name':'stid',
                              'Latitude (°N)':'lat_installation',
                              'Longitude (°E)':'lon_installation',
                              'Elevation (wgs84 m)':'alt_installation'})
                                          
for station in df_meta_gcnet.stid:
    try:
        path_to_gcnet = 'C:/Users/bav/OneDrive - GEUS/Code/PROMICE/GC-Net-Level-1-data-processing/L1/'
        df_aws = nead.read(path_to_gcnet+'daily/'+station.replace(' ','')+'_daily.csv').to_dataframe()
    except:
        path_to_gcnet = 'C:/Users/bav/OneDrive - Geological Survey of Denmark and Greenland/Code/PROMICE/GC-Net-Level-1-data-processing/L1/'
        df_aws = nead.read(path_to_gcnet+'daily/'+station.replace(' ','')+'_daily.csv').to_dataframe()

    df_aws.timestamp = pd.to_datetime(df_aws.timestamp)
    df_aws = df_aws.set_index('timestamp')
    
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
    for v in variables:
        if v not in df_aws.columns:
            df_aws[v] = np.nan
    df_aws['stid'] = station
    df_aws.index = pd.to_datetime(df_aws.index,utc=True)
    
    df_aws_all = pd.concat((df_aws_all,df_aws))

# %% export to netcdf
df_aws_all = df_aws_all.reset_index().rename(columns={'index':'time'})
df_aws_all.time = df_aws_all.time.dt.tz_localize(None)
df_aws_all = df_aws_all.set_index(['time','stid'])
ds_aws_all = df_aws_all.to_xarray()
# adding metadata
ds_aws_all = xr.merge((ds_aws_all, df_meta_promice.set_index('stid').to_xarray()))
ds_aws_all = xr.merge((ds_aws_all, df_meta_gcnet.set_index('stid').to_xarray()))

ds_aws_all.to_netcdf('data/AWS_compilation.nc')

# %% overview table
table = xr.Dataset()
for station in ds_aws_all.stid:
    table= xr.merge((table, xr.merge((
        ds_aws_all.where(ds_aws_all.stid==station, drop=True)[
            ['lat_installation','lon_installation','alt_installation','source']],
        ds_aws_all.where(ds_aws_all.stid==station, drop=True)[
            ['t_u']].dropna(dim='time').count(dim='time')))))

table.to_dataframe().to_csv('data/AWS_compilation_overview.csv')
    