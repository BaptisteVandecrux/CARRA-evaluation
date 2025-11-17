import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pandas as pd
DEFAULT_VARS = ['time','stid','t_u', 'rh_u','rh_u_cor', 'qh_u','p_u', 'wspd_u','dlr', 'ulr',
            't_surf',  'albedo', 'dsr', 'dsr_cor',  'usr',  'usr_cor','dlhf_u','dshf_u']

def load_CARRA_data(*args):
    if len(args) == 1:
        c = args[0]
        surface_input_path = c.surface_input_path
        station = c.station
    elif len(args) == 2:
        surface_input_path, station = args

    aws_ds = xr.open_dataset(surface_input_path)

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
    return df_carra

def load_promice_data(station,res,data_type, variables = DEFAULT_VARS):
    path_l3 = 'C:/Users/bav/GitHub/PROMICE data/thredds-data/'

    if data_type=='stations': folder = 'level_2_stations'
    if data_type=='sites': folder = 'level_3_sites'

    df_aws = pd.read_csv(f'{path_l3}/{folder}/csv/{res}/{station}_{res}.csv')

    df_aws.time = pd.to_datetime(df_aws.time).dt.tz_localize(None)
    df_aws=df_aws.set_index('time')
    df_aws['stid'] = station
    df_aws['stid'] = station
    return df_aws[[v for v in variables if v in df_aws.columns]]

# %% shift
        # if var == 'dsr':
        #     common_idx = (df_aws
        #                   .loc[df_aws[var].notnull()]
        #                   .index.intersection(
        #                       df_carra.loc[df_carra[var.replace('_cor','')]
        #                                    .notnull()].index))

        #     if len(common_idx)<100:
        #         print(stid, 'skipped because N<100')
        #         continue
        #     df_carra_filled = df_carra.loc[common_idx].fillna(method='ffill')
        #     df_aws_filled = df_aws.loc[common_idx].fillna(method='ffill')
        #     correlation = df_carra_filled[var.replace('_cor', '')].corr(df_aws_filled[var])
        #     max_corr = 0
        #     best_shift = 0

        #     for shift in range(-7, 7):
        #         df2_shifted = df_aws_filled.shift(shift).copy(deep=True)
        #         correlation = df_carra_filled[var.replace('_cor', '')].corr(df2_shifted[var])
        #         if correlation > max_corr:
        #             max_corr = correlation
        #             best_shift = shift

        # print("Best Shift:", best_shift)

        # df_aws = df_aws.shift(-best_shift)

# %% plot HIRHAM RH
        # if var == "rh_u":
        #     try:
        #         df_list=[]
        #         st = stid
        #         for y in range(1980,2016):
        #                 tmp= pd.read_csv(f'HIRHAM RH/{stid}_{y}_relhum.txt',
        #                                  header = None)
        #                 tmp.columns=['RH']
        #                 tmp['time'] = pd.date_range(start=f'{y}-01-01 00:00',
        #                                             periods=len(tmp), freq='3h')
        #                 tmp = tmp.set_index('time')
        #                 df_list.append(tmp)
        #         df_hh = pd.concat(df_list)
        #         df_hh['RH']=df_hh['RH']*100

        #         df_hh['RH'].plot(ax=ax1, label='HIRHAM',marker='.', alpha = 0.5)
        #     except:
        #         # plt.close(fig)
        #         pass
