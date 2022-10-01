from datetime import datetime

import numpy as np
import pandas as pd

from fuel import Fuel
from merits import DemandMerit, SupplyMerit
from utils import find_fuel_price, find_electricity_price


class EnergyConverter:
    grid_position: {"x": int, "y": int} = None

    def __init__(self, name: str, internal: bool):
        self.name = name
        self.internal = internal  # Used to determine if the system is internal to the factory or external

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other


class HeatSource(EnergyConverter):
    """
    A heat source adds a time variant thermal output to one (1) connected heat network.
    """

    def __init__(self, name: str, internal: bool = True, heat_supply: [{"supply": float, "timestamp": datetime}] = 0,
                 price: float = 0):
        EnergyConverter.__init__(self, name, internal)
        self.supply = heat_supply
        self.price = price
        self.co2_equivalent = 0

    def get_merit(self, timestamp: datetime) -> SupplyMerit:
        supply = self.get_supply(timestamp=timestamp)
        price = self.get_price(timestamp=timestamp)
        co2_equivalent = self.co2_equivalent
        return SupplyMerit(self.name, supply, price, co2_equivalent=co2_equivalent)

    def get_supply(self, timestamp):
        if isinstance(self.supply, list):
            return next((supply["supply"] for supply in self.supply
                         if supply["timestamp"] == timestamp),
                        0)

        elif isinstance(self.supply, pd.Series):
            return self.supply[timestamp]

        else:
            return self.supply

    def get_price(self, timestamp):
        if isinstance(self.price, list):
            return next((price["price"] for price in self.price
                         if price["timestamp"] == timestamp),
                        0)

        elif isinstance(self.price, pd.Series):
            return self.price[timestamp]

        else:
            return self.price

    def update_supply_at_timestamp(self, timestamp, add):
        if isinstance(self.supply, list):
            for i, supply in enumerate(self.supply):
                if supply["timestamp"] == timestamp:
                    supply["supply"] = supply["supply"] + add
                    self.supply[i] = supply
                    break

        elif isinstance(self.supply, pd.Series):
            self.supply[timestamp] = self.supply[timestamp] + add

        else:
            self.supply = self.supply + add


class HeatDemand(EnergyConverter):
    """
    A demand system is something that pulls heat out of a network.

    If a demand system is connected to a cooling system, it is a cooler. Otherwise it is something with a heat demand,
    such as a cleaning machine, a radiator for space heating etc.
    """

    def __init__(self, name: str,
                 heat_demand: [{"demand": float, "timestamp": datetime}] = 0,
                 price: float = 0, internal: bool = True):
        EnergyConverter.__init__(self, name, internal)
        self.demand = heat_demand
        self.price = price

    def get_demand_merit(self, timestamp: datetime) -> DemandMerit:
        demand = self.get_demand(timestamp)
        return DemandMerit(self.name, demand, self.price)

    def get_demand(self, timestamp: datetime = None):
        if isinstance(self.demand, list):
            # Find the fitting demand in the list by the "timestamp" key:
            demand_at_timestamp = next((demand["demand"] for demand in self.demand
                                        if demand["timestamp"] == timestamp),
                                       0)
            return demand_at_timestamp

        elif isinstance(self.demand, (int, float, np.float64)):
            return self.demand

        elif isinstance(self.demand, pd.Series):
            demand_at_timestamp = self.demand[timestamp]
            return demand_at_timestamp

        else:
            raise TypeError

    def update_demand_at_timestamp(self, timestamp, add):
        if isinstance(self.demand, list):
            for i, demand in enumerate(self.demand):
                if demand["timestamp"] == timestamp:
                    demand["demand"] = demand["demand"] + add
                    self.demand[i] = demand
                    break

        elif isinstance(self.demand, pd.Series):
            self.demand[timestamp] = self.demand[timestamp] + add

        else:
            self.demand = self.demand + add


class Boiler(HeatSource):
    """
    A boiler converts fuel(s) into thermal energy. It adds a time variant thermal output to one (1) connected
    heat network.

    A boiler has a nominal thermal power.
    A boiler converts fuel with a thermal efficiency into thermal energy
    """

    def __init__(self, name: str, internal: bool = True,
                 heat_supply: [{"supply": float, "timestamp": datetime}] = 0,
                 fuel: Fuel = Fuel(name="Natural Gas", co2_equivalent=0, calorific_value=40),
                 fuel_price_reference=None,
                 efficiency=1
                 ):
        self.fuel = fuel
        HeatSource.__init__(self, name, internal, heat_supply)
        self.efficiency = efficiency
        self.price = get_boiler_price(fuel_price_reference, self.efficiency)
        self.co2_equivalent = self.fuel.co2_equivalent / self.efficiency


class CHP(HeatSource):
    """
    A CHP converts fuel(s) into electricity and thermal energy. It adds a time variant thermal output to multiple connected
    heat networks

    The relevant CHPs for our analysis split their thermal output into Exhaust Heat and Engine heat.
    The nominal heat output can be derived from the thermal efficiency and the engine_heat and exhaust heat factors.
    If the connected heat sink is unable to take the nominal heat output, additional cooling is used. --> Usable waste heat

    A CHP has 1+ Fuel inputs consisting of fuel type and usage data
    A CHP has a nominal electrical power.
    A CHP converts fuel with a thermal efficiency into thermal energy and electricity

    A CHP has 1+ heat outputs

    CHP.data should be indexed as follows:
    Electricity output
    Fuel inputs aggregated by fuel type
    Heat outputs
    """

    def __init__(self, name: str, internal: bool = True,
                 thermal_efficiency: float = 1,
                 electrical_efficiency: float = 1,
                 electricity_supply=None,
                 heat_supply=None,
                 fuel: Fuel = Fuel(name="Natural Gas", co2_equivalent=0.247, calorific_value=40),
                 operating_mode="thermal",
                 fuel_price_reference=None,
                 electricity_price_reference=None
                 ):

        self.thermal_efficiency = thermal_efficiency
        self.electrical_efficiency = electrical_efficiency
        self.electricity_supply = electricity_supply
        self.fuel = fuel

        # If our operation mode is heat-oriented we need to calculate the price from the difference of the fuel price
        #  and the electricity price

        # If our operation mode is electricity-oriented we need to calculate the available waste heat from the
        # thermal efficiency and the electricity supply

        if operating_mode == "electric":
            if not heat_supply:
                heat_supply = self.heat_supply_from_electricity_supply()
            price = 0

        if operating_mode == "thermal":
            price = self.make_chp_price(fuel_price_reference, electricity_price_reference)

        HeatSource.__init__(self, name, internal, heat_supply=heat_supply, price=price)
        self.co2_equivalent = self.fuel.co2_equivalent / self.thermal_efficiency

    def make_chp_price(self, fuel_price_reference, electricity_price_reference):
        """
        :return:
        """
        # Default price
        price = 0.08 / self.thermal_efficiency - 0.2 * (self.electrical_efficiency / self.thermal_efficiency)

        if fuel_price_reference is not None:
            price = []
            matched_timestamps = []
            for timestamp in fuel_price_reference.index:
                matching_electricity_price = find_electricity_price(timestamp, electricity_price_reference) * (
                        self.electrical_efficiency / self.thermal_efficiency)
                fuel_price = find_fuel_price(timestamp, fuel_price_reference) / self.thermal_efficiency
                price.append({"price": fuel_price - matching_electricity_price,
                              "timestamp": timestamp})
                matched_timestamps.append(timestamp)

            if electricity_price_reference is not None:
                if len(price) < len(electricity_price_reference):
                    for timestamp in electricity_price_reference.index:
                        if timestamp not in matched_timestamps:
                            matching_fuel_price = find_fuel_price(timestamp,
                                                                  fuel_price_reference) / self.thermal_efficiency
                            electricity_price = find_electricity_price(timestamp, electricity_price_reference) \
                                                * (self.electrical_efficiency / self.thermal_efficiency)
                            price.append({"price": matching_fuel_price - electricity_price,
                                          "timestamp": timestamp})
        return price

    def heat_supply_from_electricity_supply(self):
        if type(self.electricity_supply) == list:

            return [{"supply": ((electricity_supply["supply"] / self.electrical_efficiency) * self.thermal_efficiency),
                     "timestamp": electricity_supply["timestamp"]} for electricity_supply
                    in self.electricity_supply]
        else:
            fuel_enthalpy = self.electricity_supply / self.electrical_efficiency
            return fuel_enthalpy * self.thermal_efficiency


def get_boiler_price(fuel_price_reference, efficiency):
    base_price = 0.08 / efficiency  # [(€/s) / kW]
    price = []
    if fuel_price_reference is not None:
        for timestamp in fuel_price_reference.index:
            price.append(
                {"price": find_fuel_price(timestamp, fuel_price_reference) / efficiency, "timestamp": timestamp})
        return price
    else:
        return base_price
