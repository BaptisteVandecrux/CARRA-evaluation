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
import plotly.graph_objects as go
from plotly.offline import plot
import numpy as np
import nead
from scipy.stats import linregress
abc='abcdefghijklmnopqrst'
df = pd.read_csv('./out/summary_statistics.csv')
df['order']=0
for i,var in enumerate(['t_u','p_u','wspd_u','rh_u','rh_u_cor','qh_u',
                        't_surf','ulr','dlr',
                        'usr','usr_cor','dsr','dsr_cor','albedo',
                        'dshf_u','dlhf_u']):
    df.loc[df.variable==var,'order']=i
df = df.sort_values(by='order')
df['elevation_difference'] = df.elevation_CARRA - df.elevation_aws


# %%
def plot_scatter_regression(df, x_var,  x_label, filename):

    fig,ax = plt.subplots(4,4,sharex=True, figsize=(10,15))
    plt.subplots_adjust(bottom=0.08,top=0.93,left=0.08,right=0.99,
                        wspace=0.25,hspace=0.01)
    ax = ax.flatten()
    for i,var in enumerate(df.variable.unique()):
        ax[i].axhline(0,color='k')
        x = df.loc[(df.variable == var), x_var]
        y = df.loc[(df.variable == var), 'MD']
        sc = ax[i].scatter(x, y, df.loc[(df.variable == var), 'N']/100,
            marker='o', label='MD',ls='None')
        slope, intercept, r_value, p_value, std_err = linregress(x[~np.isnan(x+y)],
                                                                 y[~np.isnan(x+y)])

        min_max = np.array([x.min(),x.max()])
        regression_line = slope * min_max + intercept
        ax[i].plot(min_max,  regression_line, color='tab:blue', ls='--', label='_nolegend_')

        y = df.loc[(df.variable == var), 'RMSD']

        ax[i].scatter(x,y, df.loc[(df.variable == var), 'N']/100,
            marker='^', label='RMSD',ls='None')
        ax[i].set_title(abc[i]+') '+var, y=1.0, pad=-14,fontweight='bold')
        ax[i].grid()
    ax[3].legend(*sc.legend_elements("sizes", num=6),ncol=5,
                 title='Days available for comparison:', frameon=True, bbox_to_anchor=(0.2,1.21))
    ax[2].legend(loc='upper center',ncol=2,frameon=True, bbox_to_anchor=(-1.4,1.16))
    fig.text(0.5, 0.04, x_label, ha='center')
    fig.savefig(filename,dpi=240)

plot_scatter_regression(df = df, x_var='elevation_difference',
                            x_label='Elevation difference between CARRA and AWS (m a.s.l.)',
                            filename='figures/scatter_elevation_diff.png')
plot_scatter_regression(df = df, x_var='elevation_aws',
                            x_label='Elevation of AWS (m a.s.l.)',
                            filename='figures/scatter_elevation.png')

df = df.loc[df.station!='SCO_L',:]
plot_scatter_regression(df = df, x_var='elevation_difference',
                            x_label='Elevation difference between CARRA and AWS (m a.s.l.)',
                            filename='figures/scatter_elevation_diff_wo_SCO_L.png')
plot_scatter_regression(df = df, x_var='elevation_aws',
                            x_label='Elevation of AWS (m a.s.l.)',
                            filename='figures/scatter_elevation_wo_SCO_L.png')
#%%
path_l3 = 'C:/Users/bav/GitHub/PROMICE data/aws-l3-dev/level_3/'
fig_folder = 'figures/CARRA_vs_AWS/'

variables = ['t_u', 'rh_u','rh_u_cor', 'qh_u','p_u', 'wspd_u','dlr', 'ulr',
            't_surf',  'albedo', 'dsr', 'dsr_cor',  'usr',  'usr_cor','dlhf_u','dshf_u']

# loading CARRA
df_carra_all = (xr.open_dataset("./data/CARRA_at_AWS.nc")
                .drop_vars([ 'x','y','surface','valid_time','spatial_ref',
                            'heightAboveGround','step'])[
    ['t2m', 'altitude_mod', 'al', 'ssrd', 'strd', 'sp', 'skt', 'si10',
     'r2', 'tp', 'slhf', 'sshf', 'tirf', 'sh2', 'stid', 'altitude', 'stru',
     'ssru', 'sf', 'rf']]
        .to_dataframe()
        .reset_index('station',drop=True)
        .rename(columns={'t2m': 't_u', 'r2': 'rh_u',
                        'si10': 'wspd_u',  'sp': 'p_u',
                        'sh2': 'qh_u', 'ssrd': 'dsr',
                        'ssru': 'usr', 'strd': 'dlr',
                        'stru': 'ulr',  'al': 'albedo',
                        'skt': 't_surf', 'slhf': 'dlhf_u',
                        'sshf': 'dshf_u', }))
df_carra_all = df_carra_all.groupby('stid').resample('D').mean()
df_carra_all = df_carra_all.reset_index()
df_carra_all['time'] = pd.to_datetime(df_carra_all.time, utc=True)

ds_aws = xr.open_dataset("./data/AWS_compilation.nc")


station_overview = df_carra_all[['stid','latitude','longitude','altitude','altitude_mod']].drop_duplicates()
station_overview['altitude_diff'] = station_overview.altitude_mod - station_overview.altitude
station_overview.to_csv('station_overview.tsv', sep='\t')

# %% Scatter all
variables = ['t_u', 'rh_u', 'qh_u', 'p_u', 'wspd_u', 'dlr', 'ulr',
 't_surf', 'albedo', 'dsr', 'usr', 'dlhf_u', 'dshf_u']
fig, ax = plt.subplots(4,4, figsize=(11, 12))
plt.subplots_adjust(hspace=0.2, wspace=0.2,top=0.95,bottom=0.05, left=0.05,right=0.95)
ax=ax.flatten()

for i, var in enumerate(variables):
    print('# '+var)
    # df_aws = df_aws_all.set_index(['time','station'])[[var]]
    df_aws = df_aws_all[[var]]
    df_aws = df_aws.loc[df_aws[var].notnull()]
    df_carra = df_carra_all.set_index(['time','stid'])[[var]]
    common_idx = df_aws.index.intersection(df_carra.index)
    df_aws = df_aws.loc[common_idx, :]
    df_carra = df_carra.loc[common_idx, :]

    RMSE = np.sqrt(np.mean((df_carra-df_aws)**2))
    ME = (df_carra - df_aws).mean().item()
    N = (df_carra - df_aws).count().item()
    # RMSE_JJA = np.sqrt(np.mean((df_carra-df_aws)**2))
    # ME_JJA = (df_carra - df_aws).mean().item()

    ax[i].plot(df_carra[var.replace('_cor', '')], df_aws[var],
             marker='.', ls='None', markersize=1,
             color='k', alpha=0.2, label=station)
    ax[i].set_title(var)
    ax[i].set_xlim(df_carra[var].quantile(0.01).item(),df_carra[var].quantile(0.99).item())
    ax[i].set_ylim(df_aws[var].quantile(0.01).item(),df_aws[var].quantile(0.99).item())
    ax[i].grid()


    # Annotate with RMSE and ME
    ax[i].annotate(f'RMSE: {RMSE:.2f}\nME: {ME:.2f}\nN: {N:.0f}',
                  xy=(0.05, 0.95), xycoords='axes fraction',
                  horizontalalignment='left', verticalalignment='top',
                  fontsize=10, bbox=dict(boxstyle="round,pad=0.3",
                                        edgecolor='black', facecolor='white'))


fig.savefig('figures/scatter_all.png', dpi=120)
# %%
fig, ax = plt.subplots(4,4, figsize=(11, 12))
plt.subplots_adjust(hspace=0.2, wspace=0.2,top=0.95,bottom=0.05, left=0.05,right=0.95)
ax=ax.flatten()

for i, var in enumerate(variables):
    print('# '+var)
    time_index = df_aws_all.index.get_level_values('time')
    df_aws = df_aws_all.loc[time_index.month.isin([6,7,8]),:][[var]]
    df_aws = df_aws.loc[df_aws[var].notnull()]
    df_carra = df_carra_all.loc[df_carra_all.time.dt.month.isin([6,7,8]),:].set_index(['time','stid'])[[var]]
    common_idx = df_aws.index.intersection(df_carra.index)
    df_aws = df_aws.loc[common_idx, :]
    df_carra = df_carra.loc[common_idx, :]

    if len(df_carra)==0:
        continue
    RMSE = np.sqrt(np.mean((df_carra-df_aws)**2))
    ME = (df_carra - df_aws).mean().item()
    N = (df_carra - df_aws).count().item()
    # RMSE_JJA = np.sqrt(np.mean((df_carra-df_aws)**2))
    # ME_JJA = (df_carra - df_aws).mean().item()

    ax[i].plot(df_carra[var.replace('_cor', '')],
             df_aws[var],
             marker='.', ls='None',
             markersize=1,
             color='tab:red',
             alpha=0.3, label=station)
    ax[i].set_title(var)
    ax[i].set_xlim(df_carra[var].quantile(0.02).item(),df_carra[var].quantile(0.98).item())
    ax[i].set_ylim(df_aws[var].quantile(0.02).item(),df_aws[var].quantile(0.98).item())
    ax[i].grid()


    # Annotate with RMSE and ME
    ax[i].annotate(f'RMSE: {RMSE:.2f}\nME: {ME:.2f}\nN: {N:.0f}',
                  xy=(0.05, 0.95), xycoords='axes fraction',
                  horizontalalignment='left', verticalalignment='top',
                  fontsize=10, bbox=dict(boxstyle="round,pad=0.3",
                                        edgecolor='black', facecolor='white'))


fig.savefig('figures/scatter_summer.png', dpi=120)

# %%

var_list = {'t_u': 'temperature',
                    'rh_u': 'relative_humidity',
                    'qh_u': 'specific_humidity',
                    'p_u': 'pressure',
                    'wspd_u': 'wind_speed',
                    'dsr': 'downward_shortwave_radiation',
                    'usr': 'upward_shortwave_radiation',
                    'albedo': 'albedo',
                    'dlr': 'downward_longwave_radiation',
                    'ulr': 'upward_longwave_radiation',
                    't_surf': 'surface_temperature',
                    'dlhf_u':'latent_heat_fluxes',
                    'dshf_u': 'sensible_heat_fluxes',
                    }

for var in var_list.keys():
    df1 = df_aws_all[['time','station',var]]
    df1['time'] = pd.to_datetime(df1['time']).values
    df2 = df_carra_all[['time','stid',var]]
    df2['time'] = pd.to_datetime(df2['time'])

    merged_df = pd.merge(df1,df2,
                         right_on=['time', 'stid'],
                         left_on=['time', 'station'])


    # Filter points for June, July, and August
    summer_points = merged_df[(merged_df['time'].dt.month >= 6) & (merged_df['time'].dt.month <= 8)]

    # Calculate mean difference and root mean squared difference for summer points
    mean_diff_summer = summer_points[var+'_x'].mean() - summer_points[var+'_y'].mean()
    rmsd_summer = ((summer_points[var+'_x'] - summer_points[var+'_y'])**2).mean()**0.5

    # Calculate mean difference and root mean squared difference for all points
    mean_diff_all = merged_df[var+'_x'].mean() - merged_df[var+'_y'].mean()
    rmsd_all = ((merged_df[var+'_x'] - merged_df[var+'_y'])**2).mean()**0.5


    # Create a scatter plot for each station
    scatter_plots = []
    for station in merged_df['station'].unique():
        data = merged_df[merged_df['station'] == station].sample(frac=0.1)
        scatter = go.Scatter(
            x=data[var+'_x'],
            y=data[var+'_y'],
            mode='markers',
            name=station
        )
        scatter_plots.append(scatter)

    # Add a 1:1 line to the plot
    one_to_one_line = go.Scatter(
        x=[merged_df[var+'_x'].min(), merged_df[var+'_x'].max()],
        y=[merged_df[var+'_y'].min(), merged_df[var+'_y'].max()],
        mode='lines',
        name='1:1 Line',
        line=dict(color='black', dash='dash')
    )

    # Create the layout for the plot
    layout = go.Layout(
        title= var_list[var].capitalize()+' scatter plot',
        xaxis=dict(title=var_list[var]+' CARRA'),
        yaxis=dict(title=var_list[var]+' AWS'),
        showlegend=True,
        annotations=[
            dict(
                x=0.05,
                y=0.9,
                xref='paper',
                yref='paper',
                text=f'Mean Diff (All): {mean_diff_all:.2f}<br>RMSD (All): {rmsd_all:.2f}'
                     f'<br>Mean Diff (Summer): {mean_diff_summer:.2f}<br>RMSD (Summer): {rmsd_summer:.2f}',
                showarrow=False,
                font=dict(size=10)
            )
        ]
    )

    # Create the figure
    fig = go.Figure(data=scatter_plots + [one_to_one_line], layout=layout)

    # Add a "Select All" option to the legend
    for scatter in scatter_plots:
        scatter['legendgroup'] = 'stations'

    # Show the plot
    plot(fig, filename='figures/'+var_list[var]+'_scatter_plot.html')

for var in var_list.keys():
    print('<iframe src="figures/html/'+var_list[var]+'_scatter_plot.html" width="800" height="600" style="border: 1px solid #ddd;"></iframe>')
    print('<p>For a full-page view, you can also <a href="figures/html/'+var_list[var]+'_scatter_plot.html" target="_blank">open the plot in a new tab</a>.</p>')
    print('')
