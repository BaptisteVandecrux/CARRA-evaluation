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
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pandas as pd 
import tocgen

path_l3 = 'C:/Users/bav/GitHub/PROMICE data/aws-l3-dev/level_3/'

filename = 'out/compil_plots.md'
f = open(filename, "w")
def Msg(txt):
    f = open(filename, "a")
    print(txt)
    f.write(txt + "\n")

df_meta = pd.read_csv(path_l3+'../AWS_latest_locations.csv')
aws_ds = xr.open_dataset("./data/CARRA_at_AWS.nc")


# station= 'KAN_L'
for station in df_meta.stid:
    Msg('## '+station)
    df_aws = pd.read_csv(path_l3 + station + '/'+station+'_day.csv')
    df_aws.time = pd.to_datetime(df_aws.time, utc=True)
    df_aws=df_aws.set_index('time')
    df_aws = df_aws.rename(columns={
                                    'dsr':'dsr_uncor', 
                                    'usr':'usr_uncor', 
                                    'dsr_cor':'dsr', 
                                    'usr_cor':'usr'
                                    })
    Msg('AWS altitude %s'%', '.join(
        df_meta.loc[df_meta.stid==station, ['alt']].astype(str).values[0].tolist())
        )
    Msg('')
    
    try:
        df_carra = aws_ds.where(aws_ds.stid==station, drop=True).squeeze().to_dataframe()
    
        # converting to a pandas dataframe and renaming some of the columns
        df_carra = df_carra.rename(columns={
                                't2m': 't_u', 
                                'r2': 'rh_u', 
                                'si10': 'wspd_u', 
                                'sp': 'p_u', 
                                'ssrd': 'dsr',
                                'ssru': 'usr',
                                'strd': 'dlr',
                                'stru': 'ulr',
                                'al': 'albedo',
                                'skt': 't_surf'
                            })
        df_carra['t_surf']  = df_carra.t_surf-273.15
        
        # Msg('CARRA altitude %s'%', '.join(
        #     df_carra[['altitude_mod', 'name']]
        #     .drop_duplicates()
        #     .astype(str).values[0].tolist())
        #     )
        
        df_carra = df_carra[
            ['t_u', 'albedo', 'dsr', 'dlr', 'p_u', 't_surf', 'wspd_u', 
             'rh_u', 'ulr', 'usr']].resample('D').mean()
        
        df_carra.index = pd.to_datetime(df_carra.index,utc=True)
        
        common_idx = df_aws.index.intersection(df_carra.index)
        df_aws = df_aws.loc[common_idx, :]
        df_carra = df_carra.loc[common_idx, :]
    
   
        plt.close('all')
        for var in ['t_u', 'albedo', 'dsr', 'dlr', 'p_u', 't_surf', 'wspd_u', 
                    'rh_u', 'ulr', 'usr']:
            ME = np.mean(df_carra[var] - df_aws[var])
            RMSE = np.sqrt(np.mean((df_carra[var] - df_aws[var])**2))
        
            fig = plt.figure(figsize=(12, 4))
            gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1]) 
            ax1 = plt.subplot(gs[0])
            ax2 = plt.subplot(gs[1])
            
            # first plot
            df_aws[var].plot(ax=ax1, label='AWS')
            df_carra[var].plot(ax=ax1,alpha=0.7, label='CARRA')
            ax1.set_ylabel(var)
            ax1.set_title(station)
            ax1.legend()
        
            # second plot
            ax2.plot(df_aws[var], df_carra[var], marker='.',ls='None')
            ax2.set_xlabel('AWS')
            ax2.set_ylabel('CARRA')
            ax2.set_title(var)
            slope, intercept, r_value, p_value, std_err = linregress(
                df_aws[var], df_carra[var])
            max_val = max(df_aws[var].max(), df_carra[var].max())
            min_val = min(df_aws[var].min(), df_carra[var].min())
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
    Msg(' ')
tocgen.processFile(filename, filename[:-3]+"_toc.md")
f.close()