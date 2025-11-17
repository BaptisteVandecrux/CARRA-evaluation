# -*- coding: utf-8 -*-
"""
Created on %(date)s
@author: bav@geus.dk

tip list:
    %matplotlib inline
    %matplotlib qt
    import pdb; pdb.set_trace()
"""

# Compute bias
bias = df_carra_all[var.replace('_cor','')] - df_aws[var]
bias = bias.dropna()

# Assign regime label to each timestamp
net_lw_full = (df_aws["dlr"] - df_aws["ulr"]).dropna()
regime = net_lw_full.rolling("7D").mean() > -4
regime.name = "regime"
regime = regime.map({True: "weak net LW", False: "strong net LW"})

# Align and clean
df_bias = pd.concat([bias, regime], axis=1).dropna()
df_bias.columns = ["bias", "regime"]

# Boxplot
plt.figure(figsize=(5, 5))
df_bias.boxplot(column="bias", by="regime")
plt.title("Bias (CARRA - AWS) vs Net LW regime")
plt.suptitle("")
plt.ylabel("Bias (W/m²)")
plt.grid()
plt.tight_layout()

from scipy.stats import ttest_ind
group_weak = df_bias[df_bias["regime"] == "weak net LW"]["bias"]
group_strong = df_bias[df_bias["regime"] == "strong net LW"]["bias"]
stat, p = ttest_ind(group_weak, group_strong, equal_var=False)
print(f"T-test p-value: {p:.4f}")

# %%

import matplotlib.pyplot as plt

fig, axs = plt.subplots(1, 2, figsize=(10, 4))

# Histogram of daily bias
axs[0].hist(bias_daily.dropna(), bins=30, color="blue", alpha=0.7)
axs[0].set_title("Daily DLR Bias (AWS - CARRA)")
axs[0].set_xlabel("Bias [W/m²]")
axs[0].set_ylabel("Frequency")
axs[0].grid(True)

# Histogram of daily net LW
axs[1].hist(net_lw_daily.dropna(), bins=30, color="orange", alpha=0.7)
axs[1].set_title("Daily Net LW (dlr - ulr)")
axs[1].set_xlabel("Net LW [W/m²]")
axs[1].grid(True)

plt.tight_layout()
plt.show()

# %%
plt.figure(figsize=(7, 4))
plt.hist(group_weak, bins=30, alpha=0.6, label="weak net LW", color="orange")
# plt.hist(group_strong, bins=30, alpha=0.6, label="strong net LW", color="blue")
plt.xlabel("Bias (CARRA - AWS) [W/m²]")
plt.ylabel("Frequency")
plt.title("Histogram of Bias under Different Net LW Regimes")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
