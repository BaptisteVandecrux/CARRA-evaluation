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
from lib import load_CARRA_data
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pandas as pd 
import tocgen
import nead
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
df_meta['source'] ='PROMICE/GEUS'
try:
    path_to_gcnet = 'C:/Users/bav/OneDrive - GEUS/Code/PROMICE/GC-Net-Level-1-data-processing/L1/'
    tmp = pd.read_csv(path_to_gcnet+'GC-Net_location.csv', skipinitialspace=True)
except:
    path_to_gcnet = 'C:/Users/bav/OneDrive - Geological Survey of Denmark and Greenland/Code/PROMICE/GC-Net-Level-1-data-processing/L1/'
    tmp = pd.read_csv(path_to_gcnet+'GC-Net_location.csv', skipinitialspace=True)
tmp['source'] = 'GC-Net historical'
df_meta = pd.concat((
    df_meta[['stid','lat_installation','lon_installation','source']],
    tmp.loc[tmp.Northing>0, ['Name','Northing','Easting','Elevationm','source']
            ].rename(columns={'Name':'stid',
                      'Northing':'lat_installation',
                      'Easting':'lon_installation',
                      'Elevationm':'alt_installation'})), ignore_index=True)
df_meta = df_meta.loc[df_meta.source=='GC-Net historical',:]

aws_ds = xr.open_dataset("./data/CARRA_at_AWS.nc")

df_summary = pd.DataFrame()

for var in ['t_u', 'rh_u','rh_u_uncor','qh_u','p_u', 'wspd_u','dlr', 'ulr',
            't_surf',  'albedo', 'dsr', 'dsr_uncor',  'usr',  'usr_uncor',
            'dlhf_u','dshf_u']:
# for var in ['dlhf_u','dshf_u']:
    Msg('# '+var)

    for station in df_meta.stid:
    # for station in ['QAS_U']:
        main_station = []
        if station == 'CEN2':
            main_station = 'CEN1'
        if 'v3' in station:
            main_station = station
            main_station=main_station.replace('v3','')
        if len(main_station)>0:
            Msg('Skipping '+station+', already used in combination with '+main_station)
            Msg('')
            continue
#%%
        try:
            df_aws = pd.read_csv(path_l3 + station + '/'+station+'_day.csv')
            df_aws.time = pd.to_datetime(df_aws.time, utc=True)
            df_aws=df_aws.set_index('time')
            df_aws = df_aws.rename(columns={
                'dsr':'dsr_uncor',  'usr':'usr_uncor', 'dsr_cor':'dsr', 'usr_cor':'usr',
                'rh_u':'rh_u_uncor','rh_u_cor':'rh_u', 'rh_l':'rh_l_uncor','rh_l_cor':'rh_l',
                                            })
        except:
            df_aws = nead.read(path_to_gcnet+'daily/'+station.replace(' ','')+'_daily.csv').to_dataframe()
            df_aws.timestamp = pd.to_datetime(df_aws.timestamp)
            df_aws = df_aws.set_index('timestamp')
            df_aws = df_aws.rename(columns={
                        'ISWR':'dsr',  'OSWR':'usr', 
                        'RH2':'rh_u_uncor','RH2_cor':'rh_u_cor', 'TA2':'t_u',
                        'VW2':'wspd_u','P':'p_u','LHF':'dlhf_u',
                        'Alb':'albedo','Q2':'sh_u','SHF':'dshf_u'
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
                'dsr':'dsr_uncor',  'usr':'usr_uncor', 'dsr_cor':'dsr', 'usr_cor':'usr',
                'rh_u':'rh_u_uncor','rh_u_cor':'rh_u', 'rh_l':'rh_l_uncor','rh_l_cor':'rh_l',
                                            })
            df_aws = df_aws.combine_first(df_sec)
            
        try:
            df_carra = aws_ds.where(aws_ds.name==station.replace('v3',''), drop=True).squeeze().to_dataframe()
        
            # converting to a pandas dataframe and renaming some of the columns
            df_carra = df_carra.rename(columns={
                't2m': 't_u', 'r2': 'rh_u',  'si10': 'wspd_u', 
                'sp': 'p_u',  'sh2': 'qh_u', 'ssrd': 'dsr',
                'ssru': 'usr', 'strd': 'dlr', 'stru': 'ulr','sshf': 'dshf_u',
                'al': 'albedo', 'skt': 't_surf', 'slhf': 'dlhf_u' })
            # df_carra['t_surf']  = df_carra.t_surf-273.15
            # df_carra['dlhf_u']  = df_carra.dlhf_u/(3*3600)  #J m-2 to W m-2
            # df_carra['dshf_u']  = df_carra.dshf_u/(3*3600)  #J m-2 to W m-2
            df_carra['qh_u']  = df_carra.qh_u*1000  # kg/kg to g/kg

            
            df_carra = df_carra.drop(columns=['name','stid']).resample('D').mean()
            df_carra.index = pd.to_datetime(df_carra.index,utc=True)

            common_idx = df_aws.loc[df_aws[var].notnull()].index.intersection(df_carra.loc[df_carra[var.replace('_uncor','')].notnull()].index)

            df_carra_filled = df_carra.loc[common_idx].resample('D').asfreq().fillna(method='ffill')
            df_aws_filled = df_aws.loc[common_idx].resample('D').asfreq().fillna(method='ffill')
            correlation = df_carra_filled[var.replace('_uncor', '')].corr(df_aws_filled[var])
            max_corr = 0
            best_shift = 0
            
            for shift in range(-10, 11):
                df2_shifted = df_aws_filled.shift(shift).copy(deep=True)
                correlation = df_carra_filled[var.replace('_uncor', '')].corr(df2_shifted[var])
                if correlation > max_corr:
                    max_corr = correlation
                    best_shift = shift
            
            print("Best Shift:", best_shift)
            
            df_aws = df_aws.shift(best_shift)  
            
            if var == 'albedo':
                df_carra = df_carra.loc[df_carra.dsr>100,:]
                df_aws = df_aws.loc[df_aws.dsr>100,:]
                
            common_idx = df_aws.index.intersection(df_carra.index)
            df_aws = df_aws.loc[common_idx, :]
            df_carra = df_carra.loc[common_idx, :]
            # if len(df_carra)==0:
            #     Msg(station+' no overlapping data')
            #     continue
       
            # plt.close('all')
    
            ME = np.mean(df_carra[var.replace('_uncor', '')] - df_aws[var])
            RMSE = np.sqrt(np.mean((df_carra[var.replace('_uncor', '')] - df_aws[var])**2))
            
            tmp = pd.DataFrame()
            tmp['var'] = [var]
            tmp['station'] = station
            tmp['latitude'] = df_meta.loc[df_meta.stid==station, 'lat_installation'].item()
            tmp['longitude'] =  df_meta.loc[df_meta.stid==station, 'lon_installation'].item()
            tmp['elevation_aws'] =  df_meta.loc[df_meta.stid==station, 'alt_installation'].item()
            tmp['elevation_CARRA'] =  aws_ds.altitude_mod.where(aws_ds.stid==station, drop=True).item()
            tmp['date_start'] = max(df_aws.index[0], df_carra.index[0])
            tmp['date_end'] = min(df_aws.index[-1], df_carra.index[-1])
            tmp['ME'] = ME
            tmp['RMSE'] = RMSE
            tmp['N'] = (df_carra[var.replace('_uncor', '')] * df_aws[var]).notnull().sum()
            df_summary = pd.concat((df_summary, tmp))
            
        
            fig = plt.figure(figsize=(12, 4))
            gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1]) 
            ax1 = plt.subplot(gs[0])
            ax2 = plt.subplot(gs[1])
            
            # first plot
            df_aws[var].plot(ax=ax1, label='AWS',marker='.')
            df_carra[var.replace('_uncor', '')].plot(ax=ax1,alpha=0.7, label='CARRA')
            ax1.set_ylabel(var)
            ax1.set_title(station)
            ax1.legend()
        
            # second plot
            ax2.plot(df_aws[var], df_carra[var.replace('_uncor', '')], marker='.',ls='None')
            ax2.set_xlabel('AWS')
            ax2.set_ylabel('CARRA')
            ax2.set_title(var)
            

            slope, intercept, r_value, p_value, std_err = linregress(
                df_aws.loc[common_idx, var], df_carra.loc[common_idx, var.replace('_uncor', '')])
            max_val = max(df_aws[var].max(), df_carra[var.replace('_uncor', '')].max())
            min_val = min(df_aws[var].min(), df_carra[var.replace('_uncor', '')].min())
            ax2.plot([min_val, max_val], [min_val, max_val], 'k-', label='1:1 Line')
            regression_line = slope * df_aws[var] + intercept
            ax2.plot(df_aws[var], regression_line, 'r-', label='Linear Regression')
            ax2.legend(loc='lower right')
        
            
            # Annotate with RMSE and ME
            ax2.annotate(f'RMSE: {RMSE:.2f}\nME: {ME:.2f}', 
                         xy=(0.05, 0.95), xycoords='axes fraction', 
                         horizontalalignment='left', verticalalignment='top',
                         fontsize=10, bbox=dict(boxstyle="round,pad=0.3",
                                                edgecolor='black', facecolor='white'))
    
            fig.savefig('figures/CARRA_vs_AWS/%s_%s.png'%(station,var))
            Msg('![](../figures/CARRA_vs_AWS/%s_%s.png)'%(station,var))
        except Exception as e:
            print(e)
            Msg('error')
            pass
        Msg(' ')
df_summary.to_csv('out/summary_statistics.csv',index=None)

#%%

# Load the dataset
data = pd.read_csv('out/summary_statistics.csv')


variables = data['var'].unique()

num_vars = len(variables)
fig, axes = plt.subplots(nrows=num_vars, ncols=1, figsize=(10, num_vars * 4))
if num_vars == 1: axes = [axes]
for i, var in enumerate(variables):
    ax = axes[i]

    # Filter data for current variable
    var_data = data[data['var'] == var]

    # Plot ME
    me_data = var_data[var_data['ME'].notna()]
    ax.plot(me_data['station'], me_data['ME'], 'bo', label='ME')

    # Plot RMSE
    rmse_data = var_data[var_data['RMSE'].notna()]
    ax.plot(rmse_data['station'], rmse_data['RMSE'], 'rx', label='RMSE')

    ax.set_title('')
    ax.grid()
    ax.set_ylabel(var)
    ax.tick_params(axis='x', rotation=45)
    ax.legend()

plt.xlabel('Station')
plt.tight_layout()
fig.savefig('figures/summary_plot.png',dpi=200)

data['ME'] = data['ME'].round(2)
data['RMSE'] = data['RMSE'].round(2)
data['date_start'] = pd.to_datetime(data['date_start']).dt.date
data['date_end'] = pd.to_datetime(data['date_end']).dt.date


text_file_path = 'out/compil_plots.md'
with open(text_file_path, 'r') as file:
    existing_content = file.read()

new_content = ("# Stats plot\n\n" + '![](../figures/summary_plot.png)\n\n'
               +"# Stats table\n\n" + data.to_markdown(index=None) 
               + "\n\n" + existing_content)

# Write the combined content back to the file
with open(text_file_path, 'w') as file:
    file.write(new_content)
    

            
#%%
tocgen.processFile(filename, filename[:-3]+"_toc.md")
