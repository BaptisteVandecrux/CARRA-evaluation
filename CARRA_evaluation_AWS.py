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
ds_carra = xr.open_dataset("./data/CARRA_at_AWS.nc")

# removing unwanted stations
unwanted= ['SCO_L', 'KPC_L',  'KPC_Lv3', 'NUK_L',  # ice sheet border, mixed pixel
           'NUK_K', 'MIT', 'ZAK_A', 'ZAK_L', 'ZAK_Lv3', 'ZAK_U', 'ZAK_Uv3', # local glaciers
           'LYN_L', 'LYN_T', 'FRE',  # local glaciers
           'KAN_B', 'NUK_B','WEG_B', # off-ice AWS
           ]
good_stations = ds_aws.stid.values[~ds_aws.stid.isin(unwanted) & ds_aws.stid.isin(ds_carra.stid)]
ds_aws = ds_aws.sel(stid=good_stations)
good_stations = ds_carra.stid.values[~ds_carra.stid.isin(unwanted) & ds_carra.stid.isin(ds_aws.stid)]
ds_carra['station'] = ds_carra.stid
ds_carra = ds_carra.sel(station=good_stations)

df_summary = pd.DataFrame()

var_list =[  'ulr', 'albedo', 'dsr', 'dsr_cor',  'usr',  'usr_cor',
            'dlhf_u','dshf_u','t_u', 'rh_u','rh_u_cor',
            'wspd_u','dlr', 'ulr',  't_surf','p_u', 'qh_u']



# %% Plotting site-specific evaluation
for var in var_list:
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
            
        df_carra = ds_carra.sel(station=station.replace('v3','')).to_dataframe().drop(columns='station')
    
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
            continue
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
        MD_jja = np.mean(df_carra.loc[df_carra.index.month.isin([6,7,8]), 
                                      var.replace('_cor', '')] - df_aws.loc[df_aws.index.month.isin([6,7,8]), 
                                                                    var])
        RMSD_jja = np.sqrt(np.mean((df_carra.loc[df_carra.index.month.isin([6,7,8]), 
                                      var.replace('_cor', '')] - df_aws.loc[df_aws.index.month.isin([6,7,8]), 
                                                                    var])**2))
        
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
        tmp['MD_jja'] = MD_jja
        tmp['RMSD_jja'] = RMSD_jja
        tmp['N'] = (df_carra[var.replace('_cor', '')] * df_aws[var]).notnull().sum()
        tmp['N_jja'] = (df_carra.loc[df_carra.index.month.isin([6,7,8]), 
                                      var.replace('_cor', '')] - df_aws.loc[df_aws.index.month.isin([6,7,8]), 
                                                                    var]).count()
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

#%% Summary plots from summary statistics

# Load the dataset
data = pd.read_csv('out/summary_statistics.csv')
data['order']=0
for i,var in enumerate(['t_u','p_u','wspd_u','rh_u','rh_u_cor','qh_u',
                        't_surf','ulr','dlr',
                        'usr','usr_cor','dsr','dsr_cor','albedo',
                        'dshf_u','dlhf_u']):
    data.loc[data.variable==var,'order']=i
data = data.sort_values(by=['order','elevation_aws'])
data = data.drop(columns=['order'])
variables = data['variable'].unique()

num_vars = len(variables)
fig, axes = plt.subplots(nrows=num_vars, ncols=1, figsize=(10, num_vars * 4))
if num_vars == 1: axes = [axes]
for i, var in enumerate(variables):
    ax = axes[i]

    # Filter data for current variable
    var_data = data[data['variable'] == var]

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

# %% Producing the variable-wise report
filename = 'out/compil_plots_by_var.md'
f = open(filename, "w")

def Msg(txt):
    f = open(filename, "a")
    print(txt)
    f.write(txt + "\n")
    
for var in var_list:
    Msg('# '+var)
    no_plot = []
    for station in ds_aws.stid.values:
        if os.path.isfile('figures/CARRA_vs_AWS/%s_%s.png'%(station,var)):
            Msg('![](../figures/CARRA_vs_AWS/%s_%s.png)'%(station,var))
            Msg(' ')
        else:
            no_plot.append(station)
    Msg('No plot for '+var+' at '+', '.join(no_plot))
    Msg(' ')

# Load the dataset
data = pd.read_csv('out/summary_statistics.csv')
data['order']=0
for i,var in enumerate(['t_u','p_u','wspd_u','rh_u','rh_u_cor','qh_u',
                        't_surf','ulr','dlr',
                        'usr','usr_cor','dsr','dsr_cor','albedo',
                        'dshf_u','dlhf_u']):
    data.loc[data.variable==var,'order']=i
data = data.sort_values(by=['order','elevation_aws'])
data = data.drop(columns=['order'])
variables = data['variable'].unique()

data['MD'] = data['MD'].round(2)
data['RMSD'] = data['RMSD'].round(2)
data['date_start'] = pd.to_datetime(data['date_start']).dt.date
data['date_end'] = pd.to_datetime(data['date_end']).dt.date

with open(filename, 'r') as file:
    existing_content = file.read()

new_content = ("# Stats plot\n\n" + '![](../figures/summary_plot.png)\n\n'
               +"# Stats table\n\n" + data.to_markdown(index=None) 
               + "\n\n" + existing_content)

# Write the combined content back to the file
with open(filename, 'w') as file:
    file.write(new_content)
    
tocgen.processFile(filename, filename[:-3]+"_toc.md")

# %% Producing the station-wise report
filename = 'out/compil_plots_by_station.md'
f = open(filename, "w")

def Msg(txt):
    f = open(filename, "a")
    print(txt)
    f.write(txt + "\n")
    
# Load the summary statistic
data = pd.read_csv('out/summary_statistics.csv')
data['MD'] = data['MD'].round(2)
data['RMSD'] = data['RMSD'].round(2)
data['date_start'] = pd.to_datetime(data['date_start']).dt.date
data['date_end'] = pd.to_datetime(data['date_end']).dt.date

with open(filename, 'r') as file:
    existing_content = file.read()

new_content = ("# Stats plot\n\n" + '![](../figures/summary_plot.png)\n\n'
               +"# Stats table\n\n" + data.to_markdown(index=None) 
               + "\n\n" + existing_content)

# Write the combined content back to the file
with open(filename, 'w') as file:
    file.write(new_content)
    
for station in ds_aws.stid.values:
    Msg('# '+station)

    Msg(data.loc[data.station == station].to_markdown(index=None) )
    Msg(' ')
    
    no_plot = []
    for var in var_list:
        if os.path.isfile('figures/CARRA_vs_AWS/%s_%s.png'%(station,var)):
            Msg('![](../figures/CARRA_vs_AWS/%s_%s.png)'%(station,var))
            Msg(' ')
        else:
            no_plot.append(var)
    Msg('No plot at '+station+' for '+', '.join(no_plot))
    Msg(' ')
    
tocgen.processFile(filename, filename[:-3]+"_toc.md")

# %% compiling all plots in pdf

import pandas as pd
import codecs
import shutil
import xarray as xr

shutil.copy('plot_compilation_src/template/plot_compilation.tex',
            'plot_compilation_src/plot_compilation.tex')
var_list = ['t_u', 'rh_u','rh_u_cor', 'qh_u','p_u', 'wspd_u','dlr', 'ulr', 
            't_surf',  'albedo', 'dsr', 'dsr_cor',  'usr',  'usr_cor','dlhf_u','dshf_u']
long_var_list = ['Near surface air temperature', 'Relative humidity','Relative humidity (w.r.t. ice)',
                 'Specific humidity','Surface pressure', 'Wind speed',
                 'Downward longwave radiation', 'Upward longwave radiation', 
            'Surface temperature',  'Albedo', 'Downward shortwave radiation',
            'Downward shortwave radiation (tilt corrected)',
            'Upward shortwave radiation',
            'Upward shortwave radiation (tilt corrected)',
            'Latenet heat flux','Sensible heat flux']
ds_aws = xr.open_dataset("./data/AWS_compilation.nc")

station_list = ds_aws.stid.values

f = open('plot_compilation_src/plot_compilation.tex', 'a', encoding="utf-8")
f.write("\n")
for var,var_long in zip(var_list, long_var_list):
    var = var.replace('_','\_')
    f.write(f"\n\\section{{{var_long}}}") 
    count = 0
    for station in station_list:
        station = station.replace('_','\_')
        f.write("\n    \\begin{figure}[!htb]")
        # f.write("\n        \\hspace{-5cm}")
        f.write(f"\n        \\IfFileExists{{../figures/CARRA_vs_AWS/{station}_{var}.png}}{{%")
        f.write(f"\n            \\includegraphics[width=\\textwidth]{{../figures/CARRA_vs_AWS/{station}_{var}.png}}%")
        f.write(f"\n         }}{{\\textbf{{Image not found: ../figures/CARRA\_vs\_AWS/{station}\_{var}.png}}}}")
        f.write("\n    \\end{figure}\n")
        count=count+1
        if count==12:
            f.write(f"\n\\clearpage\n")
            count=0
    f.write(f"\n\\clearpage\n")
f.write("\n\n\\end{document}")
f.close()


#  compiling latex file
import os
import shutil  
os.chdir('plot_compilation_src/')
os.system("pdflatex plot_compilation.tex")
os.system("pdflatex plot_compilation.tex") # needs to run twice for the toc
# os.system("pdflatex plot_compilation.tex") # needs to run twice for the toc
shutil.move('plot_compilation.pdf', '../figures/plot_compilation.pdf')

# cleanup
os.remove('plot_compilation.toc')
os.remove('plot_compilation.aux')
os.remove('plot_compilation.log')