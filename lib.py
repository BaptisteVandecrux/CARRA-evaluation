import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

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
    return df_carra