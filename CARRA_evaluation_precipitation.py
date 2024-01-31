# -*- coding: utf-8 -*-
"""
@author: bav@geus.dk

tip list:
    %matplotlib inline
    %matplotlib qt
    import pdb; pdb.set_trace()
"""
from scipy.stats import linregress
from matplotlib import gridspec
# from lib import load_CARRA_data
# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pandas as pd 
import tocgen
import matplotlib

path_l3 = 'C:/Users/bav/GitHub/PROMICE data/aws-l3-dev/level_3/'

filename = 'out/compil_plots.md'
f = open(filename, "w")
def Msg(txt):
    f = open(filename, "a")
    print(txt)
    f.write(txt + "\n")
import os
fig_folder = 'figures/CARRA_vs_AWS/'
# for f in os.listdir(fig_folder):
#     os.remove(fig_folder+f)
df_meta = pd.read_csv(path_l3+'../AWS_metadata.csv')

df_meta = df_meta.loc[df_meta.location_type == 'ice sheet']
aws_ds = xr.open_dataset("./data/CARRA_at_AWS.nc")
aws_ds = aws_ds.where(aws_ds.stid.isin(['KAN_M', 'QAS_M', 'QAS_U','TAS_A','THU_U2']),drop=True)

# %% loading sumup
df_sumup = xr.open_dataset('../SUMup/SUMup-2024/SUMup 2024 beta/SUMup_2024_SMB_greenland.nc', 
                           group='DATA').to_dataframe()
ds_meta = xr.open_dataset('../SUMup/SUMup-2024/SUMup 2024 beta/SUMup_2024_SMB_greenland.nc',
                                group='METADATA')
df_sumup.method_key = df_sumup.method_key.replace(np.nan,-9999)
df_sumup['method'] = ds_meta.method.sel(method_key = df_sumup.method_key.values).astype(str)
df_sumup['name'] = ds_meta.name.sel(name_key = df_sumup.name_key.values).astype(str)
df_sumup['reference'] = (ds_meta.reference
                         .drop_duplicates(dim='reference_key')
                         .sel(reference_key=df_sumup.reference_key.values)
                         .astype(str))
df_sumup['reference_short'] = (ds_meta.reference_short
                         .drop_duplicates(dim='reference_key')
                         .sel(reference_key=df_sumup.reference_key.values)
                         .astype(str))
df_ref = ds_meta.reference.to_dataframe()

# selecting Greenland metadata measurements
df_meta = df_sumup.loc[df_sumup.latitude>0, 
                  ['latitude', 'longitude', 'name_key', 'name', 'method_key',
                   'reference_short','reference', 'reference_key']
                  ].drop_duplicates()


# % finding the closest profile to given coordinates
# easiest if you use the following function
from scipy.spatial import distance
from math import sin, cos, sqrt, atan2, radians

def get_distance(point1, point2):
    R = 6370
    lat1 = radians(point1[0])  #insert value
    lon1 = radians(point1[1])
    lat2 = radians(point2[0])
    lon2 = radians(point2[1])

    dlon = lon2 - lon1
    dlat = lat2- lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return distance

for lat_aws, lon_aws in zip(aws_ds.latitude.values, aws_ds.longitude.values):
    # break
    query_point = [[lat_aws, lon_aws]] # NGRIP
    all_points = df_meta[['latitude', 'longitude']].values
    df_meta['distance_from_query_point'] = distance.cdist(all_points, query_point, get_distance)
    min_dist = 5 # in km
    df_meta_selec = df_meta.loc[df_meta.distance_from_query_point<min_dist, :]   
       
    # % plotting individual smb records
    cmap = matplotlib.cm.get_cmap('tab10')
    
    fig = plt.figure(figsize=(10,10))
    
    for count, ref in enumerate(df_meta_selec.reference_short.unique()):
        # each reference will be plotted in a different color
        label = ref
        for n in df_meta_selec.loc[df_meta_selec.reference_short==ref, 'name'].unique():
            # for each core or each point along a radar transect, a separate line needs
            # to be plotted
            df_stack = (df_sumup.loc[df_sumup.name==n,['start_year','end_year']]
                        .sort_values(by='start_year')
                        .stack().reset_index().drop(columns='level_1')
                        .rename(columns={0:'year'}))
            df_stack['smb'] = df_sumup.loc[df_stack.measurement_id, 'smb'].values
            df_stack.plot(ax=plt.gca(), x='year', y='smb',
                          color = cmap(count),
                          label=label, alpha=0.7, legend=False
                          )
            plt.legend(loc='upper left')
            plt.ylabel('SMB (m w.e. yr-1)')
            label='_nolegend_'
    tmp = (aws_ds
     .where((aws_ds.latitude==lat_aws) & (aws_ds.longitude==lon_aws), 
            drop=True)[['tp']]
     .isel(station=0)
     .to_dataframe()[['tp']]
     .resample('Y').sum())
    tmp['year'] = tmp.index.year
    tmp = tmp.set_index('year')/1000
    tmp.plot(ax=plt.gca(),marker='^', lw=2, c='k')
    plt.xlim(1980, 2024)
    plt.title('Observations within '+str(min_dist)+' km of '+(aws_ds
     .where((aws_ds.latitude==lat_aws) & (aws_ds.longitude==lon_aws), 
            drop=True)
     .name.values[0]))
    fig.savefig('figures/precipitation/'+  \
                (aws_ds
                 .where((aws_ds.latitude==lat_aws) & (aws_ds.longitude==lon_aws), 
                        drop=True)
                 .name.values[0])  \
                    +'.png', dpi=120)



# %% loading SnowFox
cut_off_temp = 0
aws_ds['Snowfallmweq'] = xr.where(aws_ds.t2m < cut_off_temp, 
                                  aws_ds.tp,
                                  0)
aws_ds['Snowfallmweq_2'] = aws_ds.tp - aws_ds.tirf
aws_ds['Rainfallmweq'] = xr.where(aws_ds.t2m >= cut_off_temp, 
                                  aws_ds.tp,
                                  0)
plt.close('all')
cmap = matplotlib.cm.get_cmap('tab10')
  
for station in ['KAN_M', 'QAS_M', 'QAS_U','TAS_A','THU_U2']:
    
    file = '../SUMup/SUMup-2024/data/SMB data/to add/SnowFox_GEUS/SF_'+station+'.txt'
    
    df_sf = pd.read_csv(file,delim_whitespace=True)
    df_sf[df_sf==-999] = np.nan
    df_sf['time'] = pd.to_datetime(df_sf[['Year','Month','Day']])
    df_sf = df_sf.set_index('time')
    df_sf['SWE_mweq'] =df_sf['SWE(cmWeq)']*10


    query_point = [[aws_ds.where(aws_ds.name==station,drop=True).latitude.values[0], 
                    aws_ds.where(aws_ds.name==station,drop=True).longitude.values[0]]]
    
    all_points = df_meta[['latitude', 'longitude']].values
    df_meta['distance_from_query_point'] = distance.cdist(all_points, query_point, get_distance)
    min_dist = 15 # in km
    df_meta_selec = df_meta.loc[df_meta.distance_from_query_point<min_dist, :]   
    
    
    # plotting coordinates
    # plt.figure()
    # df_meta[['latitude','longitude']].plot.scatter(ax=plt.gca(),
    #                                                 x='longitude',y='latitude')
    # plt.gca().plot(np.array(query_point)[:,1],
    #             np.array(query_point)[:,0], marker='^', 
    #             ls='None', label='target',
    #             color='tab:red')
    # df_meta_selec.plot(ax=plt.gca(), x='longitude', y='latitude',
    #               label='closest', marker='d',ls='None', color='tab:orange')
    # plt.legend()
    
    fig = plt.figure(figsize=(10,10))
    print(station)
    for count, ref in enumerate(df_meta_selec.reference_short.unique()):
        # each reference will be plotted in a different color
        label = ref
        for n in df_meta_selec.loc[df_meta_selec.reference_short==ref, 'name'].unique():
            tmp = df_sumup.loc[df_sumup.name==n,:]
            for start, end, smb, ref_short in zip(tmp.start_date, tmp.end_date, tmp.smb, tmp.reference_short):
                if smb>0.5:
                    if start>pd.to_datetime('2018-01-01'):
                        print('   ',start,end, np.round(smb*1000),ref_short)
                        plt.plot([end, end], [0, smb*1000],
                                  color = cmap(count),
                                  marker='o',
                                  label='_nolegend_',
                                  )
    start_carra = df_sf.SWE_mweq.first_valid_index()
    df_sf.SWE_mweq = df_sf.SWE_mweq -  df_sf.loc[ df_sf.SWE_mweq.first_valid_index(), 'SWE_mweq']

    df_sf.SWE_mweq.plot(ax=plt.gca(), marker='o', label='SnowFox')
    (aws_ds.where(aws_ds.name==station,drop=True).isel(station=0)['Snowfallmweq']
     .to_dataframe().Snowfallmweq.loc[start_carra:'2019-05-01']
     .cumsum()).plot(ax=plt.gca(), c='k', label='CARRA (tp when t2m>0)')
    (aws_ds.where(aws_ds.name==station,drop=True).isel(station=0)['Snowfallmweq_2']
     .to_dataframe().Snowfallmweq_2.loc[start_carra:'2019-05-01']
     .cumsum()).plot(ax=plt.gca(), c='tab:red', label='CARRA (tp-tirf)')
    if df_sf.index.year[-1]==2020:
        (aws_ds.where(aws_ds.name==station,drop=True)
         .isel(station=0)['Snowfallmweq'].to_dataframe()
         .Snowfallmweq.loc['2019-08-12':'2020-05-01']
         .cumsum()).plot(ax=plt.gca(),c='k', label='__nolegend__')
        (aws_ds.where(aws_ds.name==station,drop=True)
         .isel(station=0)['Snowfallmweq_2'].to_dataframe()
         .Snowfallmweq_2.loc['2019-08-12':'2020-05-01']
         .cumsum()).plot(ax=plt.gca(),c='tab:red', label='__nolegend__')
    plt.title(station)
    plt.legend()

    plt.title('Observations within '+str(min_dist)+' km of '+ station)
    # fig.savefig('figures/precipitation/'+  \
    #             (aws_ds
    #              .where((aws_ds.latitude==lat_aws) & (aws_ds.longitude==lon_aws), 
    #                     drop=True)
    #              .name.values[0])  \
    #                 +'.png', dpi=120)


