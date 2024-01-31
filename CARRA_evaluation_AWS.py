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
ds_aws = xr.open_dataset("./data/AWS_compilation.nc")
ds_carra = xr.open_dataset("./data/CARRA_at_AWS_20240130.nc")

df_summary = pd.DataFrame()
# %% 
for var in [  'ulr', 'albedo', 'dsr', 'dsr_cor',  'usr',  'usr_cor',
            'dlhf_u','dshf_u','t_u', 'rh_u','rh_u_cor',
                      'wspd_u','dlr', 'ulr',
                                  't_surf','p_u',   'qh_u',]:
    Msg('# '+var)

    for station in ds_aws.stid.values:
        if station not in ds_carra.stid.values:
            print(station, 'not in CARRA file')
            continue
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
        df_aws = (ds_aws.where(ds_aws.stid==station,drop=True)
                  .to_dataframe()[[var]]
                  .reset_index('stid',drop=True))
        df_aws = df_aws.dropna()
        if len(df_aws)==0:
            print('no',var,'at',station)
            continue
        
        sec_station=[]
        if station == 'CEN1':
            sec_station = 'CEN2'
        if (station+'v3' in ds_aws.stid):
            sec_station = station+'v3'
        if len(sec_station)>0:
            df_sec = (ds_aws.where(ds_aws.stid==sec_station,drop=True)
                      .to_dataframe()[[var]]
                      .reset_index('stid',drop=True))
            df_sec = df_sec.dropna()
            df_aws = df_aws.combine_first(df_sec)
            
        df_carra = ds_carra.where(ds_carra.name==station.replace('v3',''), drop=True).squeeze().to_dataframe()
    
        # converting to a pandas dataframe and renaming some of the columns
        df_carra = df_carra.rename(columns={
            't2m': 't_u', 'r2': 'rh_u',  'si10': 'wspd_u', 
            'sp': 'p_u',  'sh2': 'qh_u', 'ssrd': 'dsr',
            'ssru': 'usr', 'strd': 'dlr', 'stru': 'ulr','sshf': 'dshf_u',
            'al': 'albedo', 'skt': 't_surf', 'slhf': 'dlhf_u' })

        df_carra['qh_u']  = df_carra.qh_u*1000  # kg/kg to g/kg

        df_carra = df_carra.drop(columns=['name','stid']).resample('D').mean()

        common_idx = (df_aws
                      .loc[df_aws[var].notnull()]
                      .index.intersection(
                          df_carra.loc[df_carra[var.replace('_cor','')]
                                       .notnull()].index))
        
        if len(common_idx)<100:
            print(station, 'skipped because N<100')
        df_carra_filled = df_carra.loc[common_idx].resample('D').asfreq().fillna(method='ffill')
        df_aws_filled = df_aws.loc[common_idx].resample('D').asfreq().fillna(method='ffill')
        correlation = df_carra_filled[var.replace('_cor', '')].corr(df_aws_filled[var])
        max_corr = 0
        best_shift = 0
        
        for shift in range(-10, 11):
            df2_shifted = df_aws_filled.shift(shift).copy(deep=True)
            correlation = df_carra_filled[var.replace('_cor', '')].corr(df2_shifted[var])
            if correlation > max_corr:
                max_corr = correlation
                best_shift = shift
        
        print("Best Shift:", best_shift)
        
        df_aws = df_aws.shift(best_shift)  
        
        # if var == 'albedo':
        #     df_carra = df_carra.loc[df_carra.dsr>100,:]
        #     df_aws = df_aws.loc[df_aws.dsr>100,:]
            
        df_carra_all = df_carra.copy()
        common_idx = df_aws.index.intersection(df_carra.index)
        df_aws = df_aws.loc[common_idx, :]
        df_carra = df_carra.loc[common_idx, :]

        MD = np.mean(df_carra[var.replace('_cor', '')] - df_aws[var])
        RMSD = np.sqrt(np.mean((df_carra[var.replace('_cor', '')] - df_aws[var])**2))
        
        tmp = pd.DataFrame()
        tmp['var'] = [var]
        tmp['station'] = station
        tmp['latitude'] = ds_aws.where(ds_aws.stid==station, drop=True)['lat_installation'].item()
        tmp['longitude'] =  ds_aws.where(ds_aws.stid==station, drop=True)['lon_installation'].item()
        tmp['elevation_aws'] =  ds_aws.where(ds_aws.stid==station, drop=True)['alt_installation'].item()
        tmp['elevation_CARRA'] =  ds_carra.altitude_mod.where(ds_carra.stid==station, drop=True).item()
        tmp['date_start'] = max(df_aws.index[0], df_carra.index[0])
        tmp['date_end'] = min(df_aws.index[-1], df_carra.index[-1])
        tmp['MD'] = MD
        tmp['RMSD'] = RMSD
        tmp['N'] = (df_carra[var.replace('_cor', '')] * df_aws[var]).notnull().sum()
        df_summary = pd.concat((df_summary, tmp))
        
        fig = plt.figure(figsize=(12, 4))
        gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1]) 
        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        
        # first plot
        df_aws[var].resample('D').asfreq().plot(ax=ax1, label='AWS',marker='.')
        df_carra_all[var.replace('_cor', '')].plot(ax=ax1,alpha=0.7, label='CARRA')
        ax1.set_ylabel(var)
        ax1.set_xlim(df_aws[var].dropna().index[[0,-1]])
        ax1.set_title(station)
        ax1.legend()
    
        # second plot
        ax2.plot(df_aws[var], df_carra[var.replace('_cor', '')], marker='.',ls='None')
        ax2.set_xlabel('AWS')
        ax2.set_ylabel('CARRA')
        ax2.set_title(var)
        
        common_idx = df_aws.index.intersection(df_carra.index)
        slope, intercept, r_value, p_value, std_err = linregress(
            df_aws.loc[common_idx, var], df_carra.loc[common_idx, var.replace('_cor', '')])
        max_val = max(df_aws[var].max(), df_carra[var.replace('_cor', '')].max())
        min_val = min(df_aws[var].min(), df_carra[var.replace('_cor', '')].min())
        ax2.plot([min_val, max_val], [min_val, max_val], 'k-', label='1:1 Line')
        regression_line = slope * df_aws[var] + intercept
        ax2.plot(df_aws[var], regression_line, 'r-', label='Linear Regression')
        ax2.legend(loc='lower right')
    
        
        # Annotate with RMSD and MD
        ax2.annotate(f'RMSD: {RMSD:.2f}\nMD: {MD:.2f}', 
                     xy=(0.05, 0.95), xycoords='axes fraction', 
                     horizontalalignment='left', verticalalignment='top',
                     fontsize=10, bbox=dict(boxstyle="round,pad=0.3",
                                            edgecolor='black', facecolor='white'))

        fig.savefig('figures/CARRA_vs_AWS/%s_%s.png'%(station,var),
                    bbox_inches = 'tight', dpi=240)
        Msg('![](../figures/CARRA_vs_AWS/%s_%s.png)'%(station,var))
        Msg(' ')
df_summary.rename(columns={'var':'variable'}).to_csv('out/summary_statistics.csv',index=None)

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

    # Plot MD
    me_data = var_data[var_data['MD'].notna()]
    ax.plot(me_data['station'], me_data['MD'], 'bo', label='MD')

    # Plot RMSD
    rmse_data = var_data[var_data['RMSD'].notna()]
    ax.plot(rmse_data['station'], rmse_data['RMSD'], 'rx', label='RMSD')

    ax.set_title('')
    ax.grid()
    ax.set_ylabel(var)
    ax.tick_params(axis='x', rotation=45)
    ax.legend()

plt.xlabel('Station')
plt.tight_layout()
fig.savefig('figures/summary_plot.png',dpi=200)

data['MD'] = data['MD'].round(2)
data['RMSD'] = data['RMSD'].round(2)
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
