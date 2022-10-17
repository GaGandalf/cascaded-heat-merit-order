import json

import pandas as pd

from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import HeatSource, Boiler, HeatDemand
from cascaded_heat_merit_order.factory import Factory
from cascaded_heat_merit_order.fuel import Fuel
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.network_connectors import NetworkConnector, HeatExchanger, HeatPump
from cascaded_heat_merit_order.networks import HeatNetwork


def load_from_reference(column_name: str, reference_df: pd.DataFrame):
    return reference_df[column_name]


def location_dict_to_location_object(location_dict: dict) -> Location:
    return Location(name=location_dict["name"], latitude=location_dict["latitude"],
                    longitude=location_dict["longitude"])


def get_price_and_supply_data(heat_source: dict, reference_df: pd.DataFrame = None):
    if type(heat_source['heat_supply']) == str:
        heat_supply = load_from_reference(heat_source['heat_supply'], reference_df)
    else:
        heat_supply = heat_source['heat_supply']

    if type(heat_source['price']) == str:
        price = load_from_reference(heat_source['price'], reference_df)
    else:
        price = heat_source['price']
    return heat_supply, price


def get_price_and_demand_data(heat_demand: dict, reference_df: pd.DataFrame = None):
    if type(heat_demand['heat_demand']) == str:
        demand = load_from_reference(heat_demand['heat_demand'], reference_df)
    else:
        demand = heat_demand['heat_demand']

    if type(heat_demand['price']) == str:
        price = load_from_reference(heat_demand['price'], reference_df)
    else:
        price = heat_demand['price']
    return demand, price


def fuel_dict_to_fuel_object(fuel_dict: dict) -> Fuel:
    return Fuel(name=fuel_dict['name'], co2_equivalent=fuel_dict['co2_equivalent'],
                calorific_value=fuel_dict['calorific_value'])


def heat_source_dict_to_heat_source_object(heat_source: dict, reference_df: pd.DataFrame = None):
    if heat_source['type'] == "HeatSource":
        # Load supply and price data here
        heat_supply, price = get_price_and_supply_data(heat_source, reference_df)

        return HeatSource(name=heat_source['name'], internal=heat_source['internal'], heat_supply=heat_supply,
                          price=price)

    elif heat_source['type'] == "Boiler":
        heat_supply, price = get_price_and_supply_data(heat_source)
        fuel = fuel_dict_to_fuel_object(heat_source['fuel'])
        boiler = Boiler(name=heat_source['name'], internal=heat_source['internal'], heat_supply=heat_supply, fuel=fuel,
                        efficiency=heat_source['efficiency'])
        boiler.price = price
        return boiler

    elif heat_source['type'] == "CHP":
        heat_supply, price = get_price_and_supply_data(heat_source)
        fuel = fuel_dict_to_fuel_object(heat_source['fuel'])
        raise NotImplementedError


def heat_demand_dict_to_heat_demand_object(heat_demand: dict, reference_df: pd.DataFrame = None) -> HeatDemand:
    demand, price = get_price_and_demand_data(heat_demand, reference_df)
    return HeatDemand(name=heat_demand["name"], heat_demand=demand, price=price, internal=heat_demand['internal'])


def network_dict_to_network_object(network_dict: dict, reference_df: pd.DataFrame=None) -> HeatNetwork:
    heat_sources = []
    if network_dict['heat_sources']:
        for heat_source_dict in network_dict['heat_sources']:
            heat_sources.append(heat_source_dict_to_heat_source_object(heat_source_dict, reference_df))

    heat_demands = []
    if network_dict['heat_demands']:
        for heat_demand_dict in network_dict['heat_demands']:
            heat_demands.append(heat_demand_dict_to_heat_demand_object(heat_demand_dict, reference_df))

    return HeatNetwork(name=network_dict['name'], operating_temperature=network_dict['operating_temperature'],
                       internal=network_dict['internal'], is_cooling_network=network_dict['is_cooling_network'],
                       heat_sources=heat_sources, heat_demands=heat_demands
                       )


def network_connector_dict_to_network_connector_object(network_connector_dict: dict) -> NetworkConnector:
    if network_connector_dict["type"] == 'HeatPump':
        return HeatPump(name=network_connector_dict['name'], heat_sink=network_connector_dict['heat_sink'],
                        heat_source=network_connector_dict['heat_source'],
                        max_throughput=network_connector_dict['max_throughput'],
                        price=network_connector_dict['price'],
                        efficiency=network_connector_dict['efficiency'])

    elif network_connector_dict["type"] == 'HeatExchanger':
        return HeatExchanger(name=network_connector_dict['name'], heat_sink=network_connector_dict['heat_sink'],
                             heat_source=network_connector_dict['heat_source'],
                             max_throughput=network_connector_dict['max_throughput'],
                             price=network_connector_dict['price'],
                             efficiency=network_connector_dict['efficiency'])

    elif network_connector_dict["type"] == 'NetworkConnector':
        return NetworkConnector(name=network_connector_dict['name'], heat_sink=network_connector_dict['heat_sink'],
                                heat_source=network_connector_dict['heat_source'],
                                max_throughput=network_connector_dict['max_throughput'],
                                price=network_connector_dict['price'],
                                efficiency=network_connector_dict['efficiency'])
    else:
        raise TypeError(
            f"Type {network_connector_dict['type']} found for {network_connector_dict['name']} not defined.")


def factory_dict_to_factory_object(factory_dict: dict, reference_df: pd.DataFrame = None) -> Factory:
    networks = []
    if factory_dict['networks']:
        for network_dict in factory_dict['networks']:
            networks.append(network_dict_to_network_object(network_dict, reference_df))

    dhs_dict = factory_dict["dhs"]
    if dhs_dict:
        dhs = DHS(name=dhs_dict["name"], location=location_dict_to_location_object(dhs_dict["location"]),
                  min_temp=dhs_dict["minimum_feed_in_temperature"],
                  max_temp=dhs_dict["maximum_feed_in_temperature"])
    else:
        dhs = None

    network_connectors = []
    if factory_dict["network_connectors"]:
        for network_connector_dict in factory_dict["network_connectors"]:
            network_connectors.append(network_connector_dict_to_network_connector_object(network_connector_dict))

    factory = Factory(name=factory_dict["name"], location=location_dict_to_location_object(factory_dict["location"]),
                      dhs=dhs, networks=networks, network_connectors=network_connectors)
    return factory
