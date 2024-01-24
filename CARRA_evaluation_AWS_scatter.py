# -*- coding: utf-8 -*-
"""
@author: bav@geus.dk

tip list:
    %matplotlib inline
    %matplotlib qt
    import pdb; pdb.set_trace()
"""
# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import xarray as xr
import pandas as pd 

path_l3 = 'C:/Users/bav/GitHub/PROMICE data/aws-l3-dev/level_3/'
fig_folder = 'figures/CARRA_vs_AWS/'

variables = ['t_u', 'rh_u','rh_u_cor', 'qh_u','p_u', 'wspd_u','dlr', 'ulr', 
            't_surf',  'albedo', 'dsr', 'dsr_cor',  'usr',  'usr_cor','dlhf_u','dshf_u']

df_meta = pd.read_csv(path_l3+'../AWS_metadata.csv')
df_meta = df_meta.loc[df_meta.location_type == 'ice sheet']
df_aws_all = pd.DataFrame()
for station in df_meta.stid:
    df_aws = pd.read_csv(path_l3 + station + '/'+station+'_day.csv')[['time']+variables]
    df_aws.time = pd.to_datetime(df_aws.time)
    df_aws['station'] = station
    df_aws_all = pd.concat((df_aws_all,df_aws))


df_carra_all = xr.open_dataset("./data/CARRA_at_AWS.nc")[
    ['t2m', 'altitude_mod', 'name', 'al', 'ssrd', 'strd', 'sp', 'skt', 'si10',
     'r2', 'tp', 'slhf', 'sshf', 'tirf', 'sh2', 'stid', 'altitude', 'stru', 
     'ssru', 'sf', 'rf']].to_dataframe()

df_summary = pd.DataFrame()

fig, ax = plt.subplots(4,4, figsize=(15, 15))
ax=ax.flatten()
            
for i, var in enumerate(variables):
    print('# '+var)

    for station in df_meta.stid:
    # for station in ['QAS_U']:
        main_station = []
        if station == 'CEN2':
            main_station = 'CEN1'
        if 'v3' in station:
            main_station = station
            main_station = main_station.replace('v3','')
        if len(main_station)>0:
            print('Skipping '+station+', already used in combination with '+main_station)
            print('')
            continue
            
        df_aws = pd.read_csv(path_l3 + station + '/'+station+'_day.csv')
        df_aws.time = pd.to_datetime(df_aws.time, utc=True)
        df_aws=df_aws.set_index('time')
        df_aws = df_aws.rename(columns={
                                        'dsr':'dsr_uncor', 
                                        'usr':'usr_uncor', 
                                        'dsr_cor':'dsr', 
                                        'usr_cor':'usr',
                                        'rh_u':'rh_u_uncor',
                                        'rh_u_cor':'rh_u',
                                        'rh_l':'rh_l_uncor',
                                        'rh_l_cor':'rh_l',
                                        })
        sec_station=[]
        if station == 'CEN1':
            sec_station = 'CEN2'
        if (station+'v3' in df_meta.stid):
            sec_station = station+'v3'
        if len(sec_station)>0:
            df_sec = pd.read_csv(path_l3 + sec_station + '/'+sec_station+'_day.csv')
            df_sec.time = pd.to_datetime(df_sec.time, utc=True)
            df_sec=df_sec.set_index('time')
            df_sec = df_sec.rename(columns={
                                            'dsr':'dsr_uncor', 
                                            'usr':'usr_uncor', 
                                            'dsr_cor':'dsr', 
                                            'usr_cor':'usr',
                                            'rh_u':'rh_u_uncor',
                                            'rh_u_cor':'rh_u',
                                            'rh_l':'rh_l_uncor',
                                            'rh_l_cor':'rh_l',
                                            })
            df_aws = df_aws.combine_first(df_sec)
            
        if station not in aws_ds.name:
            print(station, 'not in CARRA data')
            continue
        df_carra = aws_ds.where(aws_ds.name==station.replace('v3',''),
                                drop=True).squeeze().to_dataframe()
    
        # converting to a pandas dataframe and renaming some of the columns
        df_carra = df_carra.rename(columns={
                                't2m': 't_u', 
                                'r2': 'rh_u', 
                                'si10': 'wspd_u', 
                                'sp': 'p_u', 
                                'sh2': 'qh_u',
                                'ssrd': 'dsr',
                                'ssru': 'usr',
                                'strd': 'dlr',
                                'stru': 'ulr',
                                'al': 'albedo',
                                'skt': 't_surf',
                                'slhf': 'dlhf_u',
                                'sshf': 'dshf_u',
                            })

        
        df_carra['qh_u']  = df_carra.qh_u*1000  # kg/kg to g/kg

        
        df_carra = df_carra.drop(columns=['name','stid']).resample('D').mean()
        df_carra.index = pd.to_datetime(df_carra.index,utc=True)
        
        if var == 'albedo':
            df_carra = df_carra.loc[df_carra.dsr>100,:]
            df_aws = df_aws.loc[df_aws.dsr>100,:]
        common_idx = df_aws.index.intersection(df_carra.index)
        df_aws = df_aws.loc[common_idx, :]
        df_carra = df_carra.loc[common_idx, :]
        if len(df_carra)==0:
            print(station+' no overlapping data')
            continue
   
            
        ax[i].plot(df_carra[var.replace('_uncor', '')],
                 df_aws[var],
                 marker='.', ls='None',
                 markersize=1,
                 alpha=0.7, label=station)
        ax[i].set_title(var)
    
    
        
        # # Annotate with RMSE and ME
        # ax2.annotate(f'RMSE: {RMSE:.2f}\nME: {ME:.2f}', 
        #              xy=(0.05, 0.95), xycoords='axes fraction', 
        #              horizontalalignment='left', verticalalignment='top',
        #              fontsize=10, bbox=dict(boxstyle="round,pad=0.3",
        #                                     edgecolor='black', facecolor='white'))


fig.savefig('figures/CARRA_vs_AWS/scatter_all.png'%(station,var))

