import json

import pandas as pd

from cascaded_heat_merit_order.factory_decoder import factory_dict_to_factory_object
from cascaded_heat_merit_order.network_connectors import HeatExchanger
from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import HeatSource, Boiler, CHP, HeatDemand, Cooler
from cascaded_heat_merit_order.factory import Factory
from cascaded_heat_merit_order.factory_encoder import FactoryEncoder
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.networks import HeatNetwork
from cascaded_heat_merit_order.utils import celsius_to_kelvin


def save_simple_set_factory():
    """
    This exports a simple factory with two heat-networks.

    An HT Network @100°C
    An MT Network @ 60°C

    Demands exist within each network and vary throughout the year.
    Waste heat exist within each network and vary throughout the year.
    A Boiler

    The HT network is connected to the MT Network via HeatExchanger
    """

    ht_name = "HT Heat Network"
    mt_name = "MT Heat Network"

    reference_df = pd.read_excel("data/simple_set_factory.xlsx", index_col=0, parse_dates=True)
    reference_df.to_csv("data/simple_set_factory.csv")

    heat_sources_ht = [Boiler(name="Gas Boiler 1", heat_supply=2500, efficiency=0.9),
                       HeatSource(name="Waste Heat HT", heat_supply=reference_df.heat_Waste_Heat_HT)]
    heat_sources_mt = [HeatSource(name="Waste Heat MT", heat_supply=reference_df.heat_Waste_Heat_MT)]

    heat_demand_ht = [HeatDemand(name="Demand HT", heat_demand=reference_df.heat_Demand_HT)]
    heat_demand_mt = [HeatDemand(name="Demand MT", heat_demand=reference_df.heat_Demand_MT)]

    networks = [
        HeatNetwork(name=ht_name, operating_temperature=celsius_to_kelvin(120), heat_sources=heat_sources_ht,
                    heat_demands=heat_demand_ht),
        HeatNetwork(name=mt_name, operating_temperature=celsius_to_kelvin(80), heat_sources=heat_sources_mt,
                    heat_demands=heat_demand_mt)
    ]

    network_connectors = [HeatExchanger(name="HT to MT Heat Exchanger",
                                        heat_sink=ht_name,
                                        heat_source=mt_name
                                        )]

    factory_location = Location("factoryTestLocation", 12.01, 13.02)
    set_factory = Factory(name="Simple SET Factory", location=factory_location,
                          networks=networks, network_connectors=network_connectors)
    set_factory.register_network_connections()
    with open("data/simple_set_factory.json", "w") as output_file:
        json.dump(set_factory, output_file, cls=FactoryEncoder, indent=6)


def load_simple_set_factory():
    with open("data/simple_set_factory.json", "r") as input_file:
        factory_dict = json.load(input_file)
    reference_df = pd.read_csv("data/simple_set_factory.csv", index_col=0, parse_dates=True)
    set_factory = factory_dict_to_factory_object(factory_dict, reference_df)
    return set_factory


if __name__ == "__main__":
    save_simple_set_factory()
    load_simple_set_factory()
