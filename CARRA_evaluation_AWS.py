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
# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pandas as pd
import tocgen
import os
import lib

res = 'hour'
data_type = 'stations'
filename = 'out/compil_plots_{res}.md'
f = open(filename, "w")
def Msg(txt):
    f = open(filename, "a")
    print(txt)
    f.write(txt + "\n")

fig_folder = f'figures/CARRA_vs_AWS_{res}/'
# for f in os.listdir(fig_folder):
#     os.remove(fig_folder+f)

df_summary = pd.DataFrame()

var_list =[ 'dsr',  'usr', 'albedo', 'dsr_cor',  'usr_cor',
            'dlhf_u','dshf_u','t_u', 'rh_u','rh_u_cor',
            'wspd_u','dlr', 't_surf','p_u', 'qh_u']
# var_list =['rh_u','rh_u_cor','t_u']
station_list = [
    'CEN1', 'CEN2', 'CP1', 'DY2',
        'EGP',  'HUM','JAR', 'JAR_O', 'KAN_L', 'KAN_Lv3',
       'KAN_M', 'KAN_U', 'KPC_U', 'KPC_Uv3', 'NAE',
       'NAU',  'NEM', 'NSE', 'NUK_N','NUK_U', 'NUK_Uv3', 'QAS_A',
       'QAS_L', 'QAS_Lv3', 'QAS_M', 'QAS_Mv3', 'QAS_U', 'QAS_Uv3', 'SCO_U', 'SCO_Uv3',
       'SCO_L','SCO_Lv3',
       'SDL', 'SDM',  'SWC', 'SWC_O',
       'TAS_A', 'TAS_L', 'TAS_U', 'THU_L', 'THU_L2', 'THU_U2','THU_U2v3', 'TUN',
       'UPE_L', 'UPE_U',
       'FRE','WEG_L','RED_Lv3','NUK_K', 'ZAC_A', 'ZAC_A','ZAC_L']


# % Plotting site-specific evaluation

for stid in station_list:
# for stid in ['CEN1']:
    Msg('# '+stid)
    df_aws = lib.load_promice_data(stid, res, data_type)

    df_carra = lib.load_CARRA_data(stid)
    if res == 'day':
        df_carra = df_carra.resample('D').mean()
    else:
        df_aws = df_aws.resample('3h').mean()

    common_idx = df_aws.index.intersection(df_carra.index)

    df_aws = df_aws.loc[slice(common_idx[0], common_idx[-1]), :]
    df_carra = df_carra.loc[slice(common_idx[0], common_idx[-1]), :]
    df_carra_all = df_carra.copy()

    # for var in var_list:
    for var in ["dlr", "dsr", "dsr_cor", "usr","usr_cor"]:
        Msg('## '+var)
        fig = plt.figure(figsize=(15, 7))
        gs = gridspec.GridSpec(1, 2, width_ratios=[2.5, 1])
        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        plt.subplots_adjust(top =0.9,bottom=0.1,left=0.05, right=0.99)

        # first plot
        df_aws[var].plot(ax=ax1, label='AWS',marker='.', ls='None')
        df_carra_all[var.replace('_cor', '')].plot(ax=ax1,alpha=0.9, label='CARRA')

        ax1.set_ylabel(var)
        ax1.set_xlim(df_aws[var].dropna().index[[0,-1]])
        ax1.set_title(stid); ax1.legend()


        # second plot
        ax2.plot(df_aws[var],
                 df_carra[var.replace('_cor', '')],
                 marker='.',ls='None', label='all measurements')


        MD = np.mean(df_carra.loc[common_idx, var.replace('_cor', '')] - df_aws.loc[common_idx, var])
        RMSD = np.sqrt(np.mean((df_carra.loc[common_idx, var.replace('_cor', '')] - df_aws.loc[common_idx,var])**2))
        # Annotate with RMSD and MD
        if var in ["dlr", "dsr", "dsr_cor", "usr","usr_cor"]:
            ax1b = ax1.twinx()
            # Compute net longwave and daily means
            net_lw = (df_aws["dlr"] - df_aws["ulr"]).dropna()
            net_lw_daily = net_lw.resample("D").mean()
            low_net_weeks = net_lw_daily[net_lw_daily > -4]

            bias = (df_aws["dlr"] - df_carra["dlr"]).dropna()
            bias_daily = bias.resample("D").mean()

            # Add shaded backgrounds to ax1 for these periods
            for t in low_net_weeks.index:
                ax1.axvspan(t, t + pd.Timedelta(days=1), color="tab:pink", alpha=0.2)

            # net_lw.plot(ax=ax1b, color="k", alpha=0.4, marker='.', ls='-', label="Net LW")
            net_lw_daily.plot(ax=ax1b, drawstyle='steps-post', color="k", alpha=0.4)
            ax1b.set_ylabel("Net LW (dlr - ulr)", color="grey")
            ax1b.set_xlim(ax1.get_xlim())
            ax1.patch.set_visible(False)
            # ax1b.legend(loc="upper right")

            # days meeting both conditions
            bad_days = net_lw_daily.index[
                (net_lw_daily > -4) & (bias_daily.abs() > 25)
            ]

            # select 3‑hourly timestamps inside these days
            df_bad = df_aws[df_aws.index.normalize().isin(bad_days)].copy()

            # removing bad data
            # df_aws.loc[df_bad.index, var] = np.nan

            # plotting filtering process
            df_bad[var].plot(marker='x',ls='None', color='tab:red', alpha=0.5,ax=ax1)

            ax2.plot(df_aws.loc[df_bad.index,var],
                     df_carra.loc[df_bad.index,var.replace('_cor', '')],
                     marker='.',ls='None',label='Frost-affected', color='tab:red')
            common_idx = [t for t in common_idx if t not in df_bad.index]
            MDf = np.mean(df_carra.loc[common_idx, var.replace('_cor', '')] - df_aws.loc[common_idx, var])
            RMSDf = np.sqrt(np.mean((df_carra.loc[common_idx, var.replace('_cor', '')] - df_aws.loc[common_idx,var])**2))
            # Annotate with RMSD and MD
            ax2.annotate(f'All measurements:\nRMSD: {RMSD:.2f}\nMD: {MD:.2f}' + \
                         f'\n\nFiltered:\nRMSD: {RMSDf:.2f}\nMD: {MDf:.2f}',
                         xy=(0.05, 0.95), xycoords='axes fraction',
                         horizontalalignment='left', verticalalignment='top',
                         fontsize=10, bbox=dict(boxstyle="round,pad=0.3",
                                                edgecolor='black', facecolor='white'))
        else:

            ax2.annotate(f'All measurements:\nRMSD: {RMSD:.2f}\nMD: {MD:.2f}',
                         xy=(0.05, 0.95), xycoords='axes fraction',
                         horizontalalignment='left', verticalalignment='top',
                         fontsize=10, bbox=dict(boxstyle="round,pad=0.3",
                                                edgecolor='black', facecolor='white'))


        ax2.set_xlabel('AWS')
        ax2.set_ylabel('CARRA')
        ax2.set_title(var)

        # slope, intercept, r_value, p_value, std_err = linregress(
        #     df_aws.loc[common_idx, var], df_carra.loc[common_idx, var.replace('_cor', '')])
        max_val = max(df_aws[var].max(), df_carra[var.replace('_cor', '')].max())
        min_val = min(df_aws[var].min(), df_carra[var.replace('_cor', '')].min())
        ax2.plot([min_val, max_val], [min_val, max_val], 'k-', label='1:1 Line')
        # regression_line = slope * df_aws[var] + intercept
        # ax2.plot(df_aws[var], regression_line, 'r-', label='Linear Regression')
        ax2.legend(loc='lower right')



        fig.savefig(f'{fig_folder}/{stid}_{var}.png', bbox_inches = 'tight', dpi=240)
        Msg(f'![](../{fig_folder}/{stid}_{var}.png)')
        Msg(' ')
        plt.close(fig)

# %%  site-specific statistics
plt.close('all')

for stid in station_list:
    for var in var_list:
        Msg('# '+var)
        if stid not in ds_carra.stid.values:
            print(stid, 'not in CARRA file')
            continue
        df_aws = lib.load_promice_data(stid, res, data_type, var_list)
        df_aws = df_aws

        if len(df_aws)==0:
            print('no',var,'at',stid)
            continue

        # sec_stid=[]
        # if stid == 'CEN1':
        #     sec_stid = 'CEN2'
        # if (stid+'v3' in ds_aws.stid):
        #     sec_stid = stid+'v3'
        # if len(sec_stid)>0:
        #     df_sec = (ds_aws.where(ds_aws.stid==sec_stid,drop=True)
        #               .to_dataframe()[[var]]
        #               .reset_index('stid',drop=True))
        #     df_sec = df_sec.dropna()
        #     df_aws = df_aws.combine_first(df_sec)

        df_carra = ds_carra.sel(
            stid=stid.replace('v3','')
            ).to_dataframe().drop(columns='stid')

        # converting to a pandas dataframe and renaming some of the columns
        df_carra = df_carra.rename(columns={
            't2m': 't_u', 'r2': 'rh_u',  'si10': 'wspd_u',
            'sp': 'p_u',  'sh2': 'qh_u', 'ssrd': 'dsr',
            'ssru': 'usr', 'strd': 'dlr', 'stru': 'ulr','sshf': 'dshf_u',
            'al': 'albedo', 'skt': 't_surf', 'slhf': 'dlhf_u' })

        df_carra['qh_u']  = df_carra.qh_u*1000  # kg/kg to g/kg

        if var == 'albedo':
            df_carra = df_carra.loc[df_carra.dsr>100,:]
            df_aws = df_aws.loc[df_aws.dsr>100,:]

        df_aws = df_aws.resample('3h').mean()

        df_carra_all = df_carra.copy()
        common_idx = df_aws.index.intersection(df_carra.index)
        df_aws = df_aws.loc[common_idx, :]
        df_carra = df_carra.loc[common_idx, :]

        MD = np.mean(df_carra[var.replace('_cor', '')] - df_aws[var])
        RMSD = np.sqrt(np.mean((df_carra[var.replace('_cor', '')] - df_aws[var])**2))
        MD_jja = np.mean(df_carra.loc[df_carra.index.month.isin([6,7,8]),
                                      var.replace('_cor', '')] - df_aws.loc[df_aws.index.month.isin([6,7,8]), var])
        RMSD_jja = np.sqrt(np.mean((df_carra.loc[df_carra.index.month.isin([6,7,8]),
                                      var.replace('_cor', '')] - df_aws.loc[df_aws.index.month.isin([6,7,8]),  var])**2))

        tmp = pd.DataFrame()
        tmp['var'] = [var]
        tmp['stid'] = stid
        tmp['latitude'] = ds_carra.latitude.where(ds_carra.stid==stid, drop=True).mean() #df_aws['lat'].mean()
        tmp['longitude'] =  ds_carra.longitude.where(ds_carra.stid==stid, drop=True).mean() #df_aws['lon'].mean()
        tmp['elevation_aws'] =  ds_carra.altitude_mod.where(ds_carra.stid==stid, drop=True).mean() #df_aws['alt'].mean()
        tmp['elevation_CARRA'] =  ds_carra.altitude_mod.where(ds_carra.stid==stid, drop=True).mean()
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
    ax.plot(me_data['stid'], me_data['MD'], 'bo', label='MD')

    # Plot RMSD
    rmse_data = var_data[var_data['RMSD'].notna()]
    ax.plot(rmse_data['stid'], rmse_data['RMSD'], 'rx', label='RMSD')

    ax.set_title('')
    ax.grid()
    ax.set_ylabel(var)
    ax.tick_params(axis='x', rotation=45)
    ax.legend()

plt.xlabel('stid')
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
    for stid in ds_aws.stid.values:
        if os.path.isfile('figures/CARRA_vs_AWS/%s_%s.png'%(stid,var)):
            Msg('![](../figures/CARRA_vs_AWS/%s_%s.png)'%(stid,var))
            Msg(' ')
        else:
            no_plot.append(stid)
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

# Write the combined content back to the file
with open(filename, 'w') as file:
    file.write(new_content)

for station in ds_aws.stid.values:
    Msg('# '+station)
    if len(data.loc[data.station == station, ['latitude', 'longitude', 'elevation_aws',
           'elevation_CARRA', 'date_start', 'date_end']])>0:
        Msg(data.loc[data.station == station, ['latitude', 'longitude', 'elevation_aws',
               'elevation_CARRA', 'date_start', 'date_end']].iloc[[0],:].to_markdown(index=None) )
        Msg(' ')

        Msg(data.loc[data.station == station, ['variable', 'MD', 'RMSD', 'MD_jja',
        'RMSD_jja', 'N', 'N_jja']].to_markdown(index=None) )
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
