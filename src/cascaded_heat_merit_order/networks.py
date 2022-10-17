from datetime import datetime
from typing import List

import pandas as pd

from cascaded_heat_merit_order.energy_converters import HeatSource, HeatDemand
from cascaded_heat_merit_order.merits import DemandMerit, SupplyMerit, Merit
from cascaded_heat_merit_order.utils import find_electricity_price, find_electricity_co2_equivalence


class HeatNetwork:
    def __init__(self, name: str, operating_temperature: float, internal: bool = True, is_cooling_network: bool = False,
                 return_temperature: float = None,
                 heat_sources: [HeatSource] = None,
                 heat_demands: [HeatDemand] = None,
                 input_connections: [] = None,
                 connected_sink_networks: [] = None,
                 cooling_cost: (int, float) = 0,
                 coolers: [] = None
                 ):
        self.mo = []
        self.dmo = []
        self.smo = []
        self.name = name
        self.operating_temperature = operating_temperature
        self.return_temperature = return_temperature
        self.internal = internal

        self.heat_sources = heat_sources
        self.heat_demands = heat_demands

        self.input_connections = input_connections
        self.connected_sink_networks = connected_sink_networks

        self.is_cooling_network = is_cooling_network
        self.cooling_cost = cooling_cost
        self.coolers = coolers

    def __str__(self):
        return self.name

    def internal_merit_order(self, timestamp: datetime = datetime.now()):
        # DMO = Demand Merit Order
        # SMO = Supply Merit Order
        self.mo = []
        self.dmo = self.get_dmo(timestamp=timestamp)
        self.smo = self.get_smo(timestamp=timestamp)

        self.dmo.sort(key=lambda x: x.price)
        self.smo.sort(key=lambda x: x.price)

        # Map the cheapest supply to the cheapest demand
        self.match_supply_and_demand(self.dmo, self.smo)
        return self.mo

    def get_dmo(self, timestamp):
        dmo = []
        if self.heat_demands:
            for demand_system in self.heat_demands:
                demand_merit = demand_system.get_demand_merit(timestamp)
                if demand_merit.demand > 0:
                    dmo.append(demand_merit)
        return dmo

    def get_smo(self, timestamp, explored_networks: List[str] = None):
        internal_smo = get_internal_smo(self, timestamp)

        # If we are the origin of this SMO calculation:
        if not explored_networks:
            explored_networks = [self.name]
        else:
            explored_networks.append(self.name)

        # Check if you have child networks
        if self.input_connections:
            for input_connection in self.input_connections:
                input_source = input_connection["source"]

                # If we have already visited this network in our tree exploration, we dont want to visit it again.
                # This avoids cyclic connections
                if input_source.name in explored_networks:
                    continue

                child_smo = input_source.get_smo(timestamp, explored_networks=explored_networks)

                if child_smo:

                    # Heat Exchanger Case:
                    if input_connection["source"].operating_temperature > self.operating_temperature:
                        efficiencies = []
                        for supply_merit in child_smo:
                            # Apply avoided cooling cost in child-network
                            avoided_cooling_cost = input_source.get_cooling_cost(timestamp, supply_merit.supply)
                            supply_merit.price = supply_merit.price - avoided_cooling_cost
                            # Multiplying the price per KW/h with the efficiency gets us the specific price in the
                            # mother network
                            supply_merit.price = supply_merit.price / input_connection["efficiency"]
                            supply_merit.co2_equivalent = supply_merit.co2_equivalent / input_connection["efficiency"]

                            # Apply additional-costs (i. e. Heat Pump electricity cost) on top, should not really
                            # be applicable for heat-exchangers though
                            supply_merit.price = supply_merit.price + input_connection["penalty"]
                            supply_merit.supply = supply_merit.supply * input_connection["efficiency"]

                            inflicted_cooling_cost = self.get_cooling_cost(timestamp, supply_merit.supply)
                            supply_merit.price = supply_merit.price + inflicted_cooling_cost

                            efficiencies.append(input_connection["efficiency"])

                        child_smo.sort(key=lambda x: x.price)
                        child_smo = filter_child_smo(child_smo, limit=input_connection["max_throughput"])
                        register_connection_usage(child_smo, heat_source=input_source, heat_sink=self,
                                                  connection_type="HEX", efficiencies=efficiencies)

                    # Heat Pump Case
                    if input_connection["source"].operating_temperature < self.operating_temperature:
                        efficiencies = []
                        for supply_merit in child_smo:
                            avoided_cooling_cost = input_source.get_cooling_cost(timestamp, supply_merit.supply)
                            supply_merit.price = supply_merit.price - avoided_cooling_cost
                            cop = get_cop(input_connection["source"].operating_temperature, self.operating_temperature,
                                          input_connection["efficiency"])

                            # Adjust cost
                            supply_merit.price = apply_specific_electricity_costs(cop, supply_merit.price,
                                                                                  find_electricity_price(timestamp))
                            supply_merit.co2_equivalent = apply_specific_electricity_co2_equivalents(
                                cop, supply_merit.co2_equivalent, find_electricity_co2_equivalence(timestamp)
                            )

                            # Adjust supply
                            supply_merit.supply = supply_merit.supply + supply_merit.supply / cop

                            inflicted_cooling_cost = self.get_cooling_cost(timestamp, supply_merit.supply)
                            supply_merit.price = supply_merit.price + inflicted_cooling_cost
                            efficiencies.append(1 + 1 / cop)
                        child_smo.sort(key=lambda x: x.price)
                        child_smo = filter_child_smo(child_smo, limit=input_connection["max_throughput"])

                        register_connection_usage(child_smo, heat_source=input_source, heat_sink=self,
                                                  connection_type="HP", efficiencies=efficiencies)

                    internal_smo.extend(child_smo)
        return internal_smo

    def match_supply_and_demand(self, dmo: List[DemandMerit], smo: List[SupplyMerit]):
        if dmo and smo:
            # Take the cheapest elements
            supply_merit = smo[0]
            demand_merit = dmo[0]

            if demand_merit.demand < supply_merit.supply:
                # The demand was satisfied by the supply
                dmo.pop(0)
                # The remaining amount of heat supply from this unit at the level of the demand
                total_transfer_efficiency = supply_merit.supply / supply_merit.original_supply
                supply_at_base_network_level = (demand_merit.demand / total_transfer_efficiency)

                # As the requested amount changes, we need to change the connection usage dictionary
                if supply_merit.connections:
                    connections = update_supply_merit_connections(supply_merit, demand_merit.demand)
                else:
                    connections = None

                # Update the supply element
                supply_merit.supply = supply_merit.supply - demand_merit.demand
                supply_merit.original_supply = supply_merit.original_supply - supply_at_base_network_level
                smo[0] = supply_merit

                self.mo.append(
                    Merit(name_source=supply_merit.name, name_sink=demand_merit.name,
                          supply=demand_merit.demand, price=supply_merit.price + demand_merit.price,
                          connections=connections, original_supply=supply_at_base_network_level,
                          sink_internal=self.internal, source_internal=supply_merit.internal
                          )
                )

            elif demand_merit.demand > supply_merit.supply:
                smo.pop(0)
                demand_merit.demand = demand_merit.demand - supply_merit.supply
                dmo[0] = demand_merit
                self.mo.append(
                    Merit(name_source=supply_merit.name, name_sink=demand_merit.name,
                          supply=supply_merit.supply, price=supply_merit.price + demand_merit.price,
                          connections=supply_merit.connections, original_supply=supply_merit.original_supply,
                          sink_internal=self.internal, source_internal=supply_merit.internal)
                )

            else:
                smo.pop(0)
                dmo.pop(0)
                self.mo.append(
                    Merit(name_source=supply_merit.name, name_sink=demand_merit.name,
                          supply=supply_merit.supply, price=supply_merit.price + demand_merit.price,
                          connections=supply_merit.connections, original_supply=supply_merit.original_supply,
                          sink_internal=self.internal, source_internal=supply_merit.internal)
                )
            self.match_supply_and_demand(dmo, smo)

    def get_cooling_cost(self, timestamp, cooling_amount: float):
        if self.is_cooling_network:
            # Do we have coolers available?
            if self.coolers:
                # Use the cheapest cooler first
                cooling_capacities = []
                for cooler in self.coolers:
                    cost = cooler.get_cooling_cost(self.operating_temperature, timestamp)
                    cooling_capacities.append({"name": cooler.name, "capacity": cooler.cooling_capacity,
                                               "cost": cost})

                cooling_capacities.sort(key=lambda x: x["cost"])
                cost = 0
                remaining_cooling_amount = cooling_amount
                for cooling_capacity in cooling_capacities:
                    if remaining_cooling_amount == 0:
                        break
                    if cooling_capacity["capacity"] < cooling_amount:
                        cost = cost + cooling_capacity["capacity"] * cooling_capacity["cost"]
                        remaining_cooling_amount = remaining_cooling_amount - cooling_amount["capacity"]
                    else:
                        cost = cost + remaining_cooling_amount * cooling_capacity["cost"]
                return cost / cooling_amount
            elif isinstance(self.cooling_cost, pd.Series):
                return self.cooling_cost[timestamp]
            else:
                return self.cooling_cost
        else:
            return 0

    def get_demand(self, timestamp):
        demand = 0
        if self.heat_demands:
            for heat_demand in self.heat_demands:
                demand = demand + heat_demand.get_demand(timestamp)
        return demand


def get_internal_smo(network: HeatNetwork, timestamp: datetime = datetime.now()):
    internal_smo = []
    if network.heat_sources:
        for heat_source in network.heat_sources:
            supply_merit = heat_source.get_merit(timestamp, network.internal)
            if supply_merit.supply > 0:
                internal_smo.append(supply_merit)
    internal_smo.sort(key=lambda x: x.price)
    return internal_smo


def filter_child_smo(child_smo: List[SupplyMerit], limit):
    if limit == 0:
        return []

    if limit is not None:
        for i, supply_merit in enumerate(child_smo):
            if limit > supply_merit.supply:
                limit = limit - supply_merit.supply
            else:
                total_efficiency = supply_merit.supply / supply_merit.original_supply
                supply_merit.supply = limit
                # As we are hereby changing the merit, we need to change the original supply as well
                supply_merit.original_supply = supply_merit.supply / total_efficiency
                del child_smo[i + 1:-1]
    return child_smo


def register_connection_usage(child_smo: List[SupplyMerit], heat_source: HeatNetwork, heat_sink: HeatNetwork,
                              connection_type: str, efficiencies: List[float]
                              ):
    for supply_merit, efficiency in zip(child_smo, efficiencies):
        if not supply_merit.connections:
            supply_merit.connections = [make_connection_usage_dict_element(heat_source, heat_sink, supply_merit.supply,
                                                                           connection_type=connection_type,
                                                                           efficiency=efficiency
                                                                           )]
        else:
            supply_merit.connections.append(
                make_connection_usage_dict_element(heat_source, heat_sink, supply_merit.supply,
                                                   connection_type=connection_type,
                                                   efficiency=efficiency))
    return child_smo


def make_connection_usage_dict_element(heat_source: HeatNetwork, heat_sink: HeatNetwork, transfer_amount: (int, float),
                                       connection_type: str, efficiency: float) -> dict:
    return {"heat_source": heat_source, "heat_sink": heat_sink, "transfer_amount": transfer_amount, "connection_type":
        connection_type, "efficiency": efficiency}


def get_cop(low_temp, high_temp, efficiency) -> float:
    cop_theoretical = high_temp / (high_temp - low_temp)
    cop = cop_theoretical * efficiency
    cop = round(cop, 5)
    return cop


def apply_specific_electricity_costs(cop, original_price, electricity_price) -> float:
    adjusted_original_price = original_price * (cop / (cop + 1))
    electricity_price = electricity_price * (1 / (cop + 1))
    return adjusted_original_price + electricity_price


def apply_specific_electricity_co2_equivalents(cop, original_co2_equivalent, electricity_co2_equivalent):
    adjusted_original_co2_equivalent = original_co2_equivalent * (cop / (cop + 1))
    electricity_co2_equivalent = electricity_co2_equivalent * (1 / (cop + 1))
    return adjusted_original_co2_equivalent + electricity_co2_equivalent


def update_supply_merit_connections(supply_merit: SupplyMerit, updated_transfer: (int, float)):
    for connection_object in supply_merit.connections:
        connection_object["transfer_amount"] = updated_transfer
        updated_transfer = updated_transfer / connection_object["efficiency"]
    return supply_merit.connections
