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
# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pandas as pd
import tocgen
import os
path_l3 = 'C:/Users/bav/GitHub/PROMICE data/aws-l3-dev/level_3/'

res = 'day'

filename = 'out/compil_plots_{res}.md'
f = open(filename, "w")
def Msg(txt):
    f = open(filename, "a")
    print(txt)
    f.write(txt + "\n")

fig_folder = 'figures/CARRA_vs_AWS_{res}/'
# for f in os.listdir(fig_folder):
#     os.remove(fig_folder+f)

if res == 'day':
    ds_aws = xr.open_dataset("./data/AWS_compilation_daily.nc")
else:
    ds_aws = xr.open_dataset("./data/AWS_compilation_hourly.nc")

ds_carra = xr.open_dataset("./data/CARRA_at_AWS_20240306.nc")

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

var_list =[ 'dsr',  'ulr', 'albedo', 'dsr_cor',  'usr',  'usr_cor',
            'dlhf_u','dshf_u','t_u', 'rh_u','rh_u_cor',
            'wspd_u','dlr', 'ulr',  't_surf','p_u', 'qh_u']
# var_list =['rh_u','rh_u_cor','t_u']

ds_aws = ds_aws[var_list+['lat','lon','alt']].sel(stid=[
    'CEN1', 'CEN2', 'CP1', 'DY2',
        'EGP',  'HUM','JAR', 'JAR_O', 'KAN_L', 'KAN_Lv3',
       'KAN_M', 'KAN_U', 'KPC_U', 'KPC_Uv3', 'NAE',
       'NAU',  'NEM', 'NSE', 'NUK_N', 'NUK_U', 'NUK_Uv3', 'QAS_A',
       'QAS_L', 'QAS_Lv3', 'QAS_M', 'QAS_Mv3', 'QAS_U', 'QAS_Uv3', 'SCO_U',
       'SDL', 'SDM',  'SWC', 'SWC_O',
       'TAS_A', 'TAS_L', 'TAS_U', 'THU_L', 'THU_L2', 'THU_U2', 'TUN',
       'UPE_L', 'UPE_U', 'WEG_L',])

# %% Plotting site-specific evaluation
plt.close('all')
# fig,ax=plt.subplots(2,1)
import matplotlib.pyplot as plt
import numpy as np

plt.close('all')
for station in ds_aws.stid.values:
    print(station)
    fig, ax = plt.subplots(2, 1, figsize=(10,10), sharex=True,sharey=True)

    # Color code by year
    years = ds_aws.sel(stid=station).time.dt.year.values
    sc = ax[0].scatter(ds_aws.sel(stid=station).t_u,
                       ds_aws.sel(stid=station).rh_u,
                       c=years, cmap='viridis', s=0.5, marker='.')
    sc2 = ax[1].scatter(ds_aws.sel(stid=station).t_u,
                        ds_aws.sel(stid=station).rh_u_cor,
                        c=years, cmap='viridis', s=0.5, marker='.')

    # Calculate 0.99 percentile for each 1-degree temperature bin
    temp_bins = np.arange(-70, 11, 1)
    binned_data = ds_aws.sel(stid=station).groupby_bins("t_u", temp_bins)

    temp_bin_centers = []
    rh_u_cor_percentiles = []
    for bin_center, group in binned_data:
        if len(group.rh_u_cor) > 0:  # Only process non-empty bins
            temp_bin_centers.append(bin_center.mid)  # Center of the temperature bin
            rh_u_cor_percentiles.append(np.percentile(group.rh_u_cor, 95))

    # Plot 0.99 percentile line on rh_u_cor plot
    ax[1].plot(temp_bin_centers, rh_u_cor_percentiles, color='red', lw=3,
               label="0.95 Percentile")

    # Set plot limits
    ax[0].set_ylim(0, 120)
    ax[0].set_xlim(-70, 10)
    ax[0].grid()
    ax[1].grid()

    # Add colorbars and titles
    fig.colorbar(sc, ax=ax[0], label="Year")
    fig.colorbar(sc2, ax=ax[1], label="Year")
    fig.suptitle(station)
    ax[1].legend()
    fig.savefig(station+'_rh.png',dpi=300)
    print(wtf)
