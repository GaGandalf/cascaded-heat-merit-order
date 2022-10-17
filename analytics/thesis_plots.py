import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import ticker


def plot_emissions_allowances_and_futures_price():
    plt.rcParams["figure.figsize"] = (16, 9)
    font = {'family': 'Arial',
            'weight': 'normal',
            'size': 14}
    matplotlib.rc('font', **font)
    historical_emissions_df = pd.read_csv("data/plotting/historical_emissions_chart_export.csv", sep=";", header=0, index_col=0)
    historical_emissions_df = historical_emissions_df.transpose()
    historical_emissions_df = historical_emissions_df * pow(10, -9)

    df = pd.read_excel("data/ets_prices.xlsx", index_col=0, parse_dates=True)


    ax = historical_emissions_df.plot.bar(stacked=True)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))

    ax2 = ax.twinx()
    ax2.plot(df.index, df["Preis"], lw=4, color="black")

    ax2.set_ylabel("Preis im EU-ETS [€/tCO2e]")

    ax.set_ylabel("CO2 Äquivalente in Zirkulation [MT-CO2e]")
    ax.set_xlabel("Jahr")
    ax.set_title("EU ETS Handelsvolumen und Emissionspreis")
    plt.grid(axis='y')
    plt.tight_layout()

    labels = ["Schätzung für Ausgleichszertifikate", "Zertifikate in Zirkulation", "Emissionspreis"]
    ax.legend(labels, loc="upper center")
    for label in ax.get_xticklabels():
        label.set_rotation(0)
    plt.savefig("c02_handelsvolumen_und_preis.png")




if __name__ == "__main__":
    plot_emissions_allowances_and_futures_price()