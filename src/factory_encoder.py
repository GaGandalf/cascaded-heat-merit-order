import json
from typing import List

from dhs import DHS
from energy_converters import Boiler, CHP, HeatSource, HeatDemand, EnergyConverter
from factory import Factory
from fuel import Fuel
from network_connectors import HeatPump, HeatExchanger
from networks import HeatNetwork

from location import Location


def encode_dhs(dhs: DHS) -> dict:
    return {"name": dhs.name, "location": encode_location(dhs.location),
            "minimum_feed_in_temperature": dhs.minimum_feed_in_temperature,
            "maximum_feed_in_temperature": dhs.maximum_feed_in_temperature}


def encode_location(location: Location) -> dict:
    return vars(location)


def encode_fuel(fuel: Fuel) -> dict:
    return vars(fuel)


def make_heat_reference_string(energy_converter: EnergyConverter) -> str:
    return f"heat_{energy_converter.name}"


def make_electricity_reference_string(heat_source: HeatSource) -> str:
    return f"electricity_{heat_source.name}"


def make_price_reference_string(energy_converter: EnergyConverter) -> str:
    return f"price_{energy_converter.name}"


def make_fuel_price_reference_string(heat_source: HeatSource) -> str:
    return f"fuel_price_ref_{heat_source.name}"


def make_electricity_price_reference_string(heat_source: HeatSource) -> str:
    return f"electricity_price_ref_{heat_source.name}"


def encode_boiler(boiler: Boiler) -> dict:
    encoded_fuel = encode_fuel(boiler.fuel)

    if type(boiler.supply) == List:
        heat_supply_ref = make_heat_reference_string(boiler)
    else:
        heat_supply_ref = boiler.supply

    if type(boiler.price) == List:
        price_ref = make_price_reference_string(boiler)
    else:
        price_ref = boiler.price

    fuel_price_reference_column_string = make_fuel_price_reference_string(boiler)
    return {
        "type": "Boiler",
        "name": boiler.name,
        "internal": boiler.internal,
        "heat_supply": heat_supply_ref,
        "fuel": encoded_fuel,
        "price": price_ref,
        "efficiency": boiler.efficiency
    }


def encode_chp(chp: CHP) -> dict:
    encoded_fuel = encode_fuel(chp.fuel)

    if type(chp.supply) == List:
        heat_supply_ref = make_heat_reference_string(chp)
    else:
        heat_supply_ref = chp.supply

    if type(chp.electricity_supply) == List:
        electricity_supply_ref = make_electricity_reference_string(chp)
    else:
        electricity_supply_ref = chp.electricity_supply

    fuel_price_reference_column_string = make_fuel_price_reference_string(chp)
    electricity_price_reference_column_string = make_electricity_price_reference_string(chp)

    return {
        "type": "CHP",
        "name": chp.name,
        "internal": chp.internal,
        "thermal_efficiency": chp.thermal_efficiency,
        "electrical_efficiency": chp.electrical_efficiency,
        "electricity_supply_reference": electricity_supply_ref,
        "heat_supply": heat_supply_ref,
        "fuel": encoded_fuel,
        "operating_mode": chp.operating_mode,
        "fuel_price_reference": fuel_price_reference_column_string,
        "electricity_price_reference": electricity_price_reference_column_string,
    }


def encode_heat_source(heat_source: HeatSource) -> dict:
    if type(heat_source.supply) == List:
        heat_supply_ref = make_heat_reference_string(heat_source)
    else:
        heat_supply_ref = heat_source.supply

    if type(heat_source.price) == List:
        price_ref = make_price_reference_string(heat_source)
    else:
        price_ref = heat_source.price

    return {
        "type": "HeatSource",
        "name": heat_source.name,
        "internal": heat_source.internal,
        "heat_supply": heat_supply_ref,
        "price": price_ref
    }


def encode_heat_demand(heat_demand: HeatDemand) -> dict:
    if type(heat_demand.demand) == List:
        heat_demand_ref = make_heat_reference_string(heat_demand)
    else:
        heat_demand_ref = heat_demand.demand

    if type(heat_demand.price) == List:
        price_ref = make_price_reference_string(heat_demand)
    else:
        price_ref = heat_demand.price

    return {
        "type": "HeatDemand",
        "name": heat_demand.name,
        "internal": heat_demand.internal,
        "heat_demand": heat_demand_ref,
        "price": price_ref
    }


def encode_network(network: HeatNetwork):
    encoded_heat_sources = []
    if network.heat_sources:
        for heat_source in network.heat_sources:
            if type(heat_source) == Boiler:
                encoded_heat_sources.append(encode_boiler(heat_source))
            elif type(heat_source) == CHP:
                encoded_heat_sources.append(encode_chp(heat_source))
            else:
                encoded_heat_sources.append(encode_heat_source(heat_source))

    encoded_heat_demands = []
    if network.heat_demands:
        for heat_demand in network.heat_demands:
            encoded_heat_demands.append(encode_heat_demand(heat_demand))

    return {
        "name": network.name,
        "operating_temperature": network.operating_temperature,
        "internal": network.internal,
        "is_cooling_network": network.is_cooling_network,
        "heat_sources": encoded_heat_sources,
        "heat_demands": encoded_heat_demands,
        "cooling_cost": network.cooling_cost
    }


def encode_network_connector(network_connector):
    if type(network_connector) == HeatPump:
        network_connector_type = "HeatPump"
    elif type(network_connector) == HeatExchanger:
        network_connector_type = "HeatExchanger"
    else:
        network_connector_type = "NetworkConnector"

    return {
        "name": network_connector.name,
        "heat_sink": network_connector.heat_sink,
        "heat_source": network_connector.heat_source,
        "max_throughput": network_connector.max_throughput,
        "price": network_connector.price,
        "efficiency": network_connector.efficiency,
        "type": network_connector_type
    }


class FactoryEncoder(json.JSONEncoder):
    def default(self, factory: Factory):
        encoded_dhs = encode_dhs(factory.dhs)

        encoded_networks = []
        for network in factory.networks:
            encoded_network = encode_network(network)
            encoded_networks.append(encoded_network)

        encoded_network_connectors = []
        for network_connector in factory.network_connectors:
            encoded_network_connector = encode_network_connector(network_connector)
            encoded_network_connectors.append(encoded_network_connector)

        encoded_factory_location = encode_location(factory.location)

        return {
            "name": factory.name,
            "location": encoded_factory_location,
            "dhs": encoded_dhs,
            "networks": encoded_networks,
            "network_connectors": encoded_network_connectors
        }
