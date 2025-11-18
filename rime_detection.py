# -*- coding: utf-8 -*-
"""
@author: bav@geus.dk

tip list:
    %matplotlib inline
    %matplotlib qt
    import pdb; pdb.set_trace()
"""
from matplotlib import gridspec
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tocgen
import lib
from datetime import timedelta

res = 'hour'
data_type = 'stations'
filename = 'out/frost_rime_overview.md'

f = open(filename, "w")
def Msg(txt):
    f = open(filename, "a")
    print(txt)
    f.write(txt + "\n")

fig_folder = f'figures/rime and frost/'
# for f in os.listdir(fig_folder):
#     os.remove(fig_folder+f)

df_summary = pd.DataFrame()

var_list =[ 'dsr',  'usr', 'albedo', 'dsr_cor',  'usr_cor',
            'dlhf_u','dshf_u','t_u', 'rh_u','rh_u_cor',
            'wspd_u','dlr', 't_surf','p_u', 'qh_u']
# var_list =['rh_u','rh_u_cor','t_u']
df_stations = pd.read_csv('../PROMICE data/thredds-data/metadata/AWS_stations_metadata.csv')
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

station_list = df_stations.station_id


# % Plotting site-specific evaluation
stat = []
for stid in station_list:
# for stid in ['CEN1']:
    Msg('# '+stid)
    df_aws = lib.load_promice_data(stid, res, data_type)

    try:
        df_carra = lib.load_CARRA_data(stid)
    except Exception as e:
        print(e)
        continue
    if res == 'day':
        df_carra = df_carra.resample('D').mean()
    else:
        df_aws = df_aws.resample('3h').mean()

    common_idx = df_aws.index.intersection(df_carra.index)
    if len(common_idx) == 0:
        Msg("no temporal overlap with CARRA data")
        continue

    df_aws = df_aws.loc[slice(common_idx[0], common_idx[-1]), :]
    df_carra = df_carra.loc[slice(common_idx[0], common_idx[-1]), :]
    df_carra_all = df_carra.copy()

    # for var in var_list:
    # for var in ["dlr", "dsr", "dsr_cor", "usr","usr_cor"]:
    for var in ["dlr", "dsr"]:
        fig = plt.figure(figsize=(15, 7))
        gs = gridspec.GridSpec(1, 2, width_ratios=[2.5, 1])
        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        plt.subplots_adjust(top =0.9,bottom=0.1,left=0.05, right=0.99)

        # first plot
        df_aws[var].plot(ax=ax1, label='all measurements',marker='.', ls='None')
        # df_carra_all[var.replace('_cor', '')].plot(ax=ax1,alpha=0.9, label='CARRA')

        ax1.set_ylabel(var)
        if len(df_aws[var].dropna())>0:
            ax1.set_xlim(df_aws[var].dropna().index[[0,-1]])
        else:
            Msg(f'no {var} data')
            continue
        ax1.set_title(stid)

        # second plot
        ax2.plot(df_aws[var],
                 df_carra[var.replace('_cor', '')],
                 marker='.',ls='None', label='all measurements')

        MD = np.mean(df_carra.loc[common_idx, var.replace('_cor', '')] - df_aws.loc[common_idx, var])
        RMSD = np.sqrt(np.mean((df_carra.loc[common_idx, var.replace('_cor', '')] - df_aws.loc[common_idx,var])**2))
        # Annotate with RMSD and MD
        if var in ["dlr", "dsr", "dsr_cor", "usr","usr_cor"]:
            # Compute net longwave and daily means
            net_lw = (df_aws["dlr"] - df_aws["ulr"])
            net_lw_daily = net_lw.resample("D").mean()
            low_net_weeks = net_lw_daily[net_lw_daily > -4]

            bias = (df_aws["dlr"] - df_carra["dlr"])
            bias_daily = bias.resample("D").mean()

            mask = (bias_daily+net_lw_daily).notnull()
            bias_daily=bias_daily.loc[mask]
            net_lw_daily=net_lw_daily.loc[mask]



            # Add shaded backgrounds to ax1 for these periods
            if len(low_net_weeks)>0:
                for t in low_net_weeks.index[:-1]:
                    ax1.axvspan(t, t + pd.Timedelta(days=1), color="tab:pink", alpha=0.2)
                t = low_net_weeks.index[-1]
                ax1.axvspan(t, t + pd.Timedelta(days=1), color="tab:pink", alpha=0.2,
                            label='days with frost or rime')

            ax1b = ax1.twinx()
            # net_lw.plot(ax=ax1b, color="k", alpha=0.4, marker='.', ls='-', label="Net LW")
            if len(net_lw_daily)>0:
                net_lw_daily.plot(ax=ax1b, drawstyle='steps-post', color="k", alpha=0.4)
            ax1b.set_ylabel("Net LW (dlr - ulr)", color="grey")
            ax1b.set_xlim(ax1.get_xlim())
            ax1b.tick_params(axis='y', colors='grey')

            ax1.patch.set_visible(False)
            # ax1b.legend(loc="upper right")

            # days meeting both conditions
            bad_days = net_lw_daily.index[
                (net_lw_daily > -4) & (bias_daily.abs() > 25)
            ]

            # select 3‑hourly timestamps inside these days
            df_bad = df_aws[df_aws.index.normalize().isin(bad_days)]

            stat.append([stid,(len(df_bad.index)/len(df_aws.index)*100)])

            # extracting periods with rime
            # 1) Create bad_daily boolean Series
            bad = bad_days
            if len(bad)>0:
                bad_daily = pd.Series(False, index=pd.date_range(bad.min(), bad.max(), freq="D"))
                bad_daily.loc[bad] = True

                # 2) Inflate bad_daily
                bad_daily_inflate = bad_daily.copy()
                bad_daily_inflate |= bad_daily.shift(1, fill_value=False)
                bad_daily_inflate |= bad_daily.shift(-1, fill_value=False)

                # 3) Deflate inflated version
                bad_daily_inflate_deflate = bad_daily_inflate.copy()
                bad_daily_inflate_deflate &= bad_daily_inflate.shift(1, fill_value=True)
                bad_daily_inflate_deflate &= bad_daily_inflate.shift(-1, fill_value=True)

                # 4) Extract contiguous periods
                from itertools import groupby
                from operator import itemgetter

                true_days = bad_daily_inflate_deflate[bad_daily_inflate_deflate].index
                groups = []
                for k, g in groupby(enumerate(true_days), lambda x: x[0] - x[1].toordinal()):
                    g = list(map(itemgetter(1), g))
                    groups.append([g[0], g[-1]])

                table = pd.DataFrame(groups, columns=["t0", "t1"])
                table=table.loc[table.t1!=table.t0]
                table['t1'] = table['t1']+pd.to_timedelta('1D')
                table['variable'] = 'dlr ulr dsr usr'
                table['comment'] = 'automatically detected as rime-affected (bav)'
                table['URL_graphic'] = 'https://github.com/GEUS-Glaciology-and-Climate/PROMICE-AWS-data-issues/issues/61'
                table.to_csv(f'flags/{stid}.csv', index=None)

                # plotting filtering process
                df_bad[var].plot(marker='x',ls='None', color='tab:red', alpha=0.5,
                                 label='frost or rime-affected measurements', ax=ax1)

                ax2.plot(df_aws.loc[df_bad.index,var],
                         df_carra.loc[df_bad.index,var.replace('_cor', '')],
                         marker='.',ls='None',
                         label='frost or rime-affected measurments', color='tab:red')
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
        if 'sr' in var:
            ax1.legend(loc='upper left')
        else:
            ax1.legend(loc='lower left')

        fig.savefig(f'{fig_folder}/{stid}_{var}.png', bbox_inches = 'tight', dpi=240)
        Msg(f'![](../{fig_folder}/{stid}_{var}.png)')
        Msg(' ')
        plt.close(fig)
stat_df = pd.DataFrame(stat, columns=['station','incidence_%']).drop_duplicates()
stat_df.to_csv('stat.csv', sep='\t', index=None, float_format='%.2f')
tocgen.processFile(filename, filename[:-3]+"_toc.md")
