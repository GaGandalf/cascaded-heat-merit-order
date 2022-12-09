from datetime import datetime
from datetime import timedelta

import numpy as np
import pandas as pd

from cascaded_heat_merit_order.fuel import Fuel
from cascaded_heat_merit_order.merits import DemandMerit, SupplyMerit
from cascaded_heat_merit_order.utils import find_fuel_price, find_electricity_price, find_ambient_temperature


class EnergyConverter:
    grid_position: {"x": int, "y": int} = None

    def __init__(self, name: str, internal: bool):
        self.name = name
        self.internal = internal  # Used to determine if the system is internal to the factory or external

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other


class HeatStorage(EnergyConverter):
    """
    Simplified Heat-Storage Unit




    Price Threshold:
    Activated after all internal demands have been met

    Do we fill the Storage, or emtpy it?

    Store it cheap, sell it expensive

    If we can sell our heat for a profit, we sell to the DHS
    If we cant sell our heat for a profit, say as the DHS has cheap sources active, we fill the storage as long as we
    stay below the user defined price_threshold.

    We empty the storage either A: to fulfill internal demands if we cant meet them otherwise or B, to gain profits by
    selling to the DHS


    Heat Loss:

    """

    def __init__(self, name: str, capacity: float, level: pd.Series, internal: bool = True, fill_threshold: float = 0,
                 empty_threshold: float = 0, min_level=100, co2_eqv=0, operation_mode = None):
        EnergyConverter.__init__(self, name, internal)
        self.capacity = capacity
        self.level = level
        self.fill_threshold = fill_threshold
        self.empty_threshold = empty_threshold
        self.operation_mode = operation_mode
        self.min_level = min_level
        self.co2eqv = co2_eqv

    def change_level(self, delta, timestamp):
        if isinstance(self.level, pd.Series):
            self.level[timestamp] = self.level[timestamp] + delta
            self.level[self.level.index > timestamp] = self.level[timestamp]
        else:
            self.level = self.level + delta

    def get_operation_mode(self, timestamp):
        if isinstance(self.operation_mode, pd.Series):
            try:
                return self.operation_mode[timestamp]
            except KeyError:
                return None
        return None

    def set_operation_mode(self, mode, timestamp):
        if not isinstance(self.operation_mode, pd.Series):
            self.operation_mode = pd.Series(mode, pd.DatetimeIndex([timestamp]))
        else:
            self.operation_mode[timestamp] = mode

    def get_level(self, timestamp):
        if isinstance(self.level, list):
            return next((level["level"] for level in self.level
                         if level["timestamp"] == timestamp),
                        0)

        elif isinstance(self.level, pd.Series):
            return self.level[timestamp]

        else:
            return self.level


    def get_co2_equivalent(self, timestamp):
        if isinstance(self.co2eqv, pd.Series):
            return self.co2eqv[timestamp]
        else:
            return self.co2eqv

    def get_supply_merit(self, timestamp, internal=True) -> SupplyMerit:
        level = self.get_level(timestamp=timestamp)
        price = self.empty_threshold
        co2_equivalent = self.get_co2_equivalent(timestamp)
        return SupplyMerit(self.name, level, price, co2_equivalent=co2_equivalent, internal=internal)


    def get_demand_merit(self, timestamp, network_name) -> DemandMerit:
        demand = self.capacity - self.get_level(timestamp)
        price = self.fill_threshold
        return DemandMerit(self.name, demand, price, network_name)

class HeatSource(EnergyConverter):
    """
    A heat source adds a time variant thermal output to one (1) connected heat network.
    """

    def __init__(self, name: str, internal: bool = True, heat_supply: [{"supply": float, "timestamp": datetime}] = 0,
                 price: float = 0, primary_energy_factor = 1):
        EnergyConverter.__init__(self, name, internal)
        self.supply = heat_supply
        self.price = price
        self.co2_equivalent = 40
        self.primary_energy_factor = primary_energy_factor

    def get_merit(self, timestamp: datetime,network_name, internal=True) -> SupplyMerit:
        supply = self.get_supply(timestamp=timestamp)
        price = self.get_price(timestamp=timestamp)
        co2_equivalent = self.co2_equivalent
        return SupplyMerit(self.name, supply, price, network_name, co2_equivalent=co2_equivalent, internal=internal,
                           primary_energy_factor=self.primary_energy_factor)

    def get_supply(self, timestamp):
        if isinstance(self.supply, list):
            return next((supply["supply"] for supply in self.supply
                         if supply["timestamp"] == timestamp),
                        0)

        elif isinstance(self.supply, pd.Series):
            try:
                return self.supply[timestamp]
            except KeyError:
                return 0

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

    def get_demand_merit(self, timestamp: datetime, network_name) -> DemandMerit:
        demand = self.get_demand(timestamp)
        return DemandMerit(self.name, demand, self.price, network_name)

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
            try:
                demand_at_timestamp = self.demand[timestamp]
            except KeyError as ke:
                print(ke)
                demand_at_timestamp = 0
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
                 fuel: Fuel = Fuel(name="Natural Gas", co2_equivalent=270, calorific_value=40),
                 fuel_price_reference=None,
                 efficiency=1,
                 primary_energy_factor = 1.1
                 ):
        self.fuel = fuel
        HeatSource.__init__(self, name, internal, heat_supply, primary_energy_factor=primary_energy_factor)
        self.efficiency = efficiency
        self.price = get_boiler_price(fuel_price_reference, self.efficiency)
        self.co2_equivalent = self.fuel.co2_equivalent / self.efficiency

    def get_merit(self, timestamp: datetime, network_name, internal=True) -> SupplyMerit:
        supply = self.get_supply(timestamp=timestamp)
        price = self.get_price(timestamp=timestamp)
        co2_equivalent = self.co2_equivalent
        return SupplyMerit(self.name, supply, price,network_name, co2_equivalent=co2_equivalent, internal=internal,
                           primary_energy_factor=self.primary_energy_factor, eff_in=self.efficiency)

    def get_price(self, timestamp: datetime):
        fuel_price = find_fuel_price(timestamp)
        return fuel_price / self.efficiency + ((270 * 70) / 1000000)/self.efficiency # at 70€/ton ->        print()

class CHP(HeatSource):
    """
    A CHP converts fuel(s) into electricity and thermal energy. It adds a time variant thermal output to multiple connected
    heat networks

    The relevant CHPs for our analysis split their thermal output into Exhaust Heat and Engine heat.
    The nominal heat output can be derived from the thermal efficiency and the engine_heat and exhaust heat factors.
    If the connected heat sink is unable to take the nominal heat output, additional cooling is used. --> Usable waste heat

    A CHP has 1 Fuel input consisting of fuel type and usage data
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
                 fuel: Fuel = Fuel(name="Natural Gas", co2_equivalent=270, calorific_value=40),
                 operating_mode="thermal",
                 fuel_price_reference=None,
                 electricity_price_reference=None,
                 coupled_supply=False,
                 supply_split=None,
                 coupled_network=None,
                 coupling_waste_cost=None,
                 minimum_supply=0
                 ):

        self.thermal_efficiency = thermal_efficiency
        self.electrical_efficiency = electrical_efficiency
        self.electricity_supply = electricity_supply
        self.fuel = fuel
        self.operating_mode = operating_mode
        self.coupled_supply = coupled_supply
        self.minimum_supply = minimum_supply

        if self.coupled_supply:
            self.supply_split = supply_split
            self.coupled_network = coupled_network
            self.coupling_waste_cost = coupling_waste_cost

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

    def get_supply(self, timestamp):
        if self.coupled_supply:
            split_factor = self.supply_split[0]
        else:
            split_factor = 1

        if isinstance(self.supply, list):
            return next((supply["supply"] * split_factor for supply in self.supply
                         if supply["timestamp"] == timestamp),
                        0)

        elif isinstance(self.supply, pd.Series):
            return self.supply[timestamp] * split_factor

        else:
            return self.supply * split_factor


    def make_chp_price(self, fuel_price_reference, electricity_price_reference):
        """
        :return:
        """
        # Default price
        price = 0.08 / self.thermal_efficiency - 0.2 * (self.electrical_efficiency / self.thermal_efficiency)

        if self.coupled_supply:
            price = price + self.coupling_waste_cost

        if fuel_price_reference is not None:
            price = []
            matched_timestamps = []
            for timestamp in fuel_price_reference.index:
                matching_electricity_price = find_electricity_price(timestamp, electricity_price_reference) * (
                        self.electrical_efficiency / self.thermal_efficiency)
                fuel_price = find_fuel_price(timestamp, fuel_price_reference) / self.thermal_efficiency
                current_price = fuel_price - matching_electricity_price
                if self.coupled_supply:
                    price = price + self.coupling_waste_cost
                price.append({"price": current_price,
                              "timestamp": timestamp})
                matched_timestamps.append(timestamp)

        elif electricity_price_reference is not None:
            price = []
            matched_timestamps = []
            if len(price) < len(electricity_price_reference):
                for timestamp in electricity_price_reference.index:
                    if timestamp not in matched_timestamps:
                        matching_fuel_price = find_fuel_price(timestamp,
                                                              fuel_price_reference) / self.thermal_efficiency
                        electricity_price = find_electricity_price(timestamp, electricity_price_reference) \
                                            * (self.electrical_efficiency / self.thermal_efficiency)

                        current_price = matching_fuel_price - electricity_price
                        if self.coupled_supply:
                            current_price = current_price + self.coupling_waste_cost
                        price.append({"price": current_price,
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

    def get_merit(self, timestamp: datetime,network_name, internal=True) -> SupplyMerit:
        supply = self.get_supply(timestamp=timestamp)
        price = self.get_price(timestamp=timestamp)
        co2_equivalent = self.co2_equivalent

        if self.minimum_supply > supply:
            return SupplyMerit(self.name, 0, price, network_name, co2_equivalent=co2_equivalent, internal=internal,
                               is_coupled=self.coupled_supply, minimum_supply=self.minimum_supply, primary_energy_factor=1.1)
        else:
            return SupplyMerit(self.name, supply, price, network_name, co2_equivalent=co2_equivalent, internal=internal,
                               is_coupled=self.coupled_supply, minimum_supply=self.minimum_supply, primary_energy_factor=1.1,
                               el_factor = self.electrical_efficiency/self.thermal_efficiency, eff_in=self.thermal_efficiency)

    def get_price(self, timestamp):
        fuel_price = find_fuel_price(timestamp)
        electricity_price = find_electricity_price(timestamp)
        price = fuel_price / self.thermal_efficiency - electricity_price * (self.electrical_efficiency / self.thermal_efficiency)
        if self.coupled_supply:
            price = price + self.coupling_waste_cost
        return price

class Cooler(EnergyConverter):
    def __init__(self, name: str, internal: bool = True, cooling_cost: float = 0,
                 cooling_capacity=None, ambient: bool = False, efficiency=1):
        EnergyConverter.__init__(self, name, internal)
        self.cooling_capacity = cooling_capacity
        self.ambient = ambient
        self.cooling_cost = cooling_cost
        self.efficiency = efficiency

    def get_cooling_cost(self, cooling_temp: float, timestamp: datetime = datetime.now()):
        if self.ambient:
            ambient_temperature = find_ambient_temperature(timestamp)
            electricity_price = find_electricity_price(timestamp)
            try:
                eeg_theoretical = ambient_temperature / (ambient_temperature - cooling_temp)
            except ZeroDivisionError:
                eeg_theoretical = 1000

            eeg = eeg_theoretical * self.efficiency
            eeg = round(eeg, 5)
            return electricity_price / eeg

        elif (isinstance(self.cooling_cost), pd.Series):
            return self.cooling_cost[timestamp]

        else:
            return self.cooling_cost


def get_boiler_price(fuel_price_reference, efficiency):
    base_price = 0.08 / efficiency  # [(€/s) / kW]
    price = []
    #find_fuel_price(timestamp=datetime.now())


    if fuel_price_reference is not None:
        for timestamp in fuel_price_reference.index:
            price.append(
                {"price": find_fuel_price(timestamp, fuel_price_reference) / efficiency, "timestamp": timestamp})
        return price
    else:
        return base_price
