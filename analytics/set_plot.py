import matplotlib
import pandas as pd

import matplotlib.pyplot as plt

df = pd.read_csv("merit_order_stresstest_results.csv")
plt.rcParams["figure.figsize"] = (8, 6)
font = {'family': 'Arial',
        'weight': 'normal',
        'size': 14}

matplotlib.rc('font', **font)
fix, ax = plt.subplots()

#df["n_elements"] = df["n_networks"] * (df["n_sources"] + df["n_demands"])

#df = df.sort_values("n_elements")

#ax.plot(df["n_elements"], df["time"])
for n_networks in df["n_networks"].unique():
    filtered_df = df[df["n_networks"] == n_networks]
    plt.plot(filtered_df["n_sources"] + filtered_df["n_demands"], filtered_df["time"], label=f"Anzahl Netzwerke: {n_networks}")
    print(filtered_df)

ax.legend()
ax.set_ylabel("Rechenzeit [s]")
ax.set_xlabel("Energiewandler pro Netzwerk")
ax.set_yscale('log')
ax.set_title("Cascaded Heat Merit Order Rechenzeiten")
plt.grid(axis = 'y')
plt.tight_layout()
plt.savefig("cmo_rechenzeit.png")
plt.show()