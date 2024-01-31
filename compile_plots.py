# -*- coding: utf-8 -*-
"""
@author: bav@geus.dk

tip list:
    %matplotlib inline
    %matplotlib qt
    import pdb; pdb.set_trace()
"""

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
