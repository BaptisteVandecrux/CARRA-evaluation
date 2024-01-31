import pandas as pd
import codecs
# %% updating author list
import shutil
shutil.copy('plot_compilation_src/template/plot_compilation.tex',
            'plot_compilation_src/plot_compilation.tex')
var_list = ['t_u','p_u']
station_list = ['CEN1','CEN2', 'KAN_U']

f = open('plot_compilation_src/plot_compilation.tex', 'a', encoding="utf-8")
for var in var_list:
    var = var.replace('_','\_')
    f.write(f"\n\\section{{{var}}}")
    for station in station_list:
        station = station.replace('_','\_')
        f.write("\n")
        f.write("\\begin{figure}[!htb]")
        f.write(f"\n\\caption{{Evaluation of {var} at {station}}}")
        # f.write("\n\\centering")
        f.write(f"\n\\IfFileExists{{../figures/CARRA_vs_AWS/{station}_{var}.png}}{{%")
        f.write(f"\n\\includegraphics[width=2\\textwidth]{{../figures/CARRA_vs_AWS/{station}_{var}.png}}%")
        f.write("\n}{\\textbf{Image not found: ../figures/CARRA\_vs\_AWS/CEN1\_t\_u.png}}")
        f.write("\n\\end{figure}\n")
f.write("\n\n\\end{document}")
f.close()


#  compiling latex file
import os
import shutil  
os.chdir('plot_compilation_src/')
os.system("pdflatex plot_compilation.tex")
os.system("pdflatex plot_compilation.tex") # needs to run twice for the toc
os.system("pdflatex plot_compilation.tex") # needs to run twice for the toc
shutil.move('plot_compilation.pdf', '../figures/plot_compilation.pdf')

# cleanup
os.remove('plot_compilation.toc')
os.remove('plot_compilation.aux')
os.remove('plot_compilation.log')
