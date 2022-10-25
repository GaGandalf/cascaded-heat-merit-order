import copy
import datetime
import logging
from typing import List
import pandas as pd

from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import HeatDemand, HeatSource, HeatStorage
from cascaded_heat_merit_order.network_connectors import NetworkConnector, HeatPump, HeatExchanger
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.networks import HeatNetwork
from cascaded_heat_merit_order.utils import celsius_to_kelvin


class Factory:
    def __init__(self, name: str, location: Location,
                 dhs: DHS = None,
                 networks: [HeatNetwork] = None,
                 network_connectors: [NetworkConnector] = None,
                 grid_size=None,
                 df: pd.DataFrame = None):

        self.demand_curve = None
        self.supply_curve = None
        self.name = name
        self.location = location
        self.dhs = dhs
        self.networks = networks
        self.hts = None
        self.coupled_supplies = 0

        self.network_connectors = network_connectors

        self.grid_size = grid_size
        self.mo = None
        self.mo_timestamp = None

        self.save_connections = False
        self.persistent_networks = copy.deepcopy(self.networks)


        self.df = df

    def __str__(self):
        return self.name

    def print_merit_order(self):
        if self.mo:
            for merit in self.mo:
                print(merit)
        else:
            print("No Merit Order found!")

    def register_network_connections(self):
        for network in self.networks:
            network.input_connections = None
            network.connected_sink_networks = None

        if self.network_connectors:
            for network_connector in self.network_connectors:
                source_network_name = network_connector.heat_source
                sink_network_name = network_connector.heat_sink

                self.networks = update_network_connections(self.networks, source_network_name, sink_network_name,
                                                           network_connector.price,
                                                           network_connector.max_throughput,
                                                           efficiency=network_connector.efficiency)

    def add_coupled_supply(self):
        raise NotImplementedError

    def merit_order(self, timestamp: datetime.datetime = datetime.datetime.now(), remaining_supply=True,
                    remaining_demand=True, initial=True):

        if initial:
            self.mo_timestamp = timestamp
            self.networks = copy.deepcopy(self.persistent_networks)
            self.register_network_connections()
            self.mo = None
            self.coupled_supplies = 0

        if not remaining_demand == 0 and not remaining_supply == 0:
            cheapest_merit = None

            network: HeatNetwork
            for network in self.networks:
                network.internal_merit_order(timestamp)
                if network.mo:
                    current_networks_cheapest_merit = network.mo[0]
                    if not cheapest_merit or cheapest_merit.price > current_networks_cheapest_merit.price:
                        cheapest_merit = current_networks_cheapest_merit

            coupled_merit_supply_system = None

            if not cheapest_merit:
                # If no merit could be found, terminate the process
                return

            if cheapest_merit.supply_is_coupled:

                for network in self.networks:
                    if network.heat_sources:
                        for heat_source in network.heat_sources:
                            if heat_source.name == cheapest_merit.name_source:
                                total_heat_supply = cheapest_merit.original_supply / (heat_source.supply_split[0])
                                coupled_supply = total_heat_supply * heat_source.supply_split[1]
                                coupled_merit_supply_system = heat_source
                                break

                if coupled_supply:
                    for network in self.networks:
                        if network.name == coupled_merit_supply_system.coupled_network:

                            coupled_heat_source = HeatSource(
                                name=f"Coupled Supply {coupled_merit_supply_system.name} {self.coupled_supplies}",
                                heat_supply=[{"supply": coupled_supply, "timestamp": timestamp}],
                                price=-coupled_merit_supply_system.coupling_waste_cost
                            )
                            self.coupled_supplies = self.coupled_supplies + 1
                            if network.heat_sources:
                                network.heat_sources.append(coupled_heat_source)
                            else:
                                network.heat_sources = [coupled_heat_source]

                else:
                    raise(KeyError("Could not find the coupled heat source!"))

            for i, network in enumerate(self.networks):
                # Demand updating
                if network.heat_demands:
                    for demand_system in network.heat_demands:
                        if cheapest_merit.name_sink == demand_system:
                            # Reduce or delete the demand:
                            if cheapest_merit.supply < demand_system.get_demand(timestamp):
                                demand_system.update_demand_at_timestamp(
                                    timestamp=timestamp,
                                    add=(-cheapest_merit.supply)
                                )
                            else:
                                demand_system.update_demand_at_timestamp(
                                    timestamp=timestamp,
                                    add=(-demand_system.get_demand(timestamp))
                                )


                # Storage updating
                if network.heat_storage:
                    for storage in network.heat_storage:
                        if cheapest_merit.name_sink == storage:
                            # Fill the storage
                            storage.change_level(delta=cheapest_merit.supply, timestamp=timestamp)
                            storage.set_operation_mode(mode="fill", timestamp=timestamp)
                            self.persist_storage(storage)

                        if cheapest_merit.name_source == storage:
                            storage.change_level(delta=-cheapest_merit.original_supply, timestamp=timestamp)
                            storage.set_operation_mode(mode="empty", timestamp=timestamp)
                            self.persist_storage(storage)


                # Supply updating
                if network.heat_sources:
                    for supply_system in network.heat_sources:
                        if cheapest_merit.name_source == supply_system:
                            # Reduce the source supply by the original supply
                            if coupled_merit_supply_system:
                                supply_system.update_supply_at_timestamp(timestamp=timestamp,
                                                                         add=(-cheapest_merit.original_supply/coupled_merit_supply_system.supply_split[0]))
                            else:
                                supply_system.update_supply_at_timestamp(timestamp=timestamp,
                                                                         add=(-cheapest_merit.original_supply))


            # Update the network connections
            if cheapest_merit.connections:
                supply_via = cheapest_merit.supply
                for connection in cheapest_merit.connections:
                    for connection_object in connection["heat_sink"].input_connections:
                        if connection_object["source"] == connection["heat_source"]:
                            if connection_object["source"].operating_temperature > \
                                    connection["heat_sink"].operating_temperature:
                                # Apply the efficiency factor to heat-exchangers
                                supply_via = supply_via / connection_object["efficiency"]
                            if connection_object["max_throughput"]:
                                connection_object["max_throughput"] = connection_object[
                                                                          "max_throughput"] - \
                                                                      connection["transfer_amount"]

            # Do not save the used connections#
            if self.save_connections:
                if cheapest_merit.connections:
                    for i, connection in enumerate(cheapest_merit.connections):
                        cheapest_merit.connections[i] = f"{connection['heat_source']}_{connection['heat_sink']}"
            else:
                cheapest_merit.connections = None

            if not self.mo:
                self.mo = [cheapest_merit]
            else:
                self.mo.append(cheapest_merit)

            self.merit_order(timestamp=timestamp, remaining_supply=remaining_supply, remaining_demand=remaining_demand,
                             initial=False)

    def connect_dhs(self, connection_network_name: str, connector_efficiency: float = 1,
                    connector_max_throughput: float = 100000):
        """
        Connect the

        :param connector_max_throughput:
        :param connector_efficiency:
        :param connection_network_name:
        """
        self.disconnect_dhs(ignore_no_dhs=True)
        connection_network = self.find_network_by_name(connection_network_name)
        dhs = self.dhs

        if dhs.use_demand_profile:
            if dhs.demand_profile is not None:
                dhs_heat_demand = [HeatDemand(name=dhs.name, price=0, heat_demand=dhs.demand_profile)]
            else:
                logging.info(f"No demand profile for DHS {dhs.name} found.")
                logging.info("Using default demand of 100 MW")
                dhs_heat_demand = [HeatDemand(name=f"{dhs.name}", price=0, heat_demand=100000)]
            dhs_heat_sources = None

        else:
            dhs_heat_demand = dhs.heat_demands
            dhs_heat_sources = dhs.heat_sources

        if self.dhs.minimum_feed_in_temperature > connection_network.operating_temperature:
            # HeatPump required,
            # Most favorable feed in temp is the minimum feed in temp
            dhs_network = HeatNetwork(name=dhs.name,
                                      operating_temperature=dhs.minimum_feed_in_temperature,
                                      heat_sources=dhs_heat_sources,
                                      heat_demands=dhs_heat_demand,
                                      internal=False)
            hts = HeatPump(name="DHS Heatpump", heat_sink=dhs.name, heat_source=connection_network_name,
                           max_throughput=connector_max_throughput, efficiency=connector_efficiency)
        else:
            # HeatExchanger required,
            # most favorable feed in temp is the maximum feed in temp
            dhs_network = HeatNetwork(name=dhs.name,
                                      operating_temperature=dhs.maximum_feed_in_temperature,
                                      heat_sources=dhs_heat_sources,
                                      heat_demands=dhs_heat_demand,
                                      internal=False)
            hts = HeatExchanger(name="DHS HeatExchanger", heat_sink=dhs.name, heat_source=connection_network_name,
                                max_throughput=connector_max_throughput, efficiency=connector_efficiency)

        self.networks.append(dhs_network)
        if not self.network_connectors:
            self.network_connectors = [hts]
        else:
            self.network_connectors.append(hts)

        self.hts = hts

        self.register_network_connections()
        self.persistent_networks = copy.deepcopy(self.networks)

    def disconnect_dhs(self, ignore_no_dhs=False):
        """
        Remove the DHS network from the networks list and remove the network connector.
        :return:
        """
        if not self.hts:
            if not ignore_no_dhs:
                logging.warning("No DHS network to disconnect!")
            return

        for network in self.persistent_networks:
            if network.name == self.dhs.name:
                del network

        for network_connector in self.network_connectors:
            if network_connector.name == self.hts.name:
                del network_connector

        self.hts = None
        self.networks = self.persistent_networks

    def find_network_by_name(self, network_name: str) -> HeatNetwork:
        network = next((network for network in self.networks if network.name == network_name), None)
        if not network:
            raise KeyError
        return network

    def remaining_internal_demand(self) -> float:
        remaining_internal_demand = 0
        for network in self.networks:
            if network.internal and not network.is_cooling_network:
                if network.heat_demands:
                    for heat_demand in network.heat_demands:
                        remaining_internal_demand = remaining_internal_demand + heat_demand.get_demand(
                            self.mo_timestamp)
        return remaining_internal_demand

    def remaining_internal_supply(self):
        remaining_internal_supply = 0
        for network in self.networks:
            if network.internal:
                if network.heat_sources:
                    for heat_source in network.heat_sources:
                        remaining_internal_supply = remaining_internal_supply + heat_source.get_supply(self.mo_timestamp)


    def remaining_cooling_demand(self) -> float:
        remaining_cooling_demand = 0
        for network in self.networks:
            if network.internal and network.is_cooling_network:
                if network.heat_sources:
                    for heat_source in network.heat_sources:
                        remaining_cooling_demand = remaining_cooling_demand + heat_source.get_supply(self.mo_timestamp)

    def cooling_cost(self):
        cooling_cost = 0
        for network in self.networks:
            if network.internal and network.is_cooling_network:
                if network.heat_sources:
                    cooling_cost = cooling_cost + network.cooling_cost()

    def internal_demand(self, timestamp=None) -> dict:
        internal_demand = {"network": [], "demand": []}
        for network in self.networks:
            if network.internal:
                internal_demand["network"].append(network.name)
                internal_demand["demand"].append(network.get_demand(timestamp))
        return internal_demand

    def internal_cost(self):
        if not self.mo:
            print("Please execute the merit order calculation before calculating the internal cost!")
            raise AttributeError

    def reset_networks(self):
        self.networks = copy.deepcopy(self.persistent_networks)

    def persist_storage(self, storage: HeatStorage):
        for network in self.persistent_networks:
            if network.heat_storage:
                for persistent_storage in network.heat_storage:
                    if storage.name == persistent_storage.name:
                        persistent_storage.level = copy.deepcopy(storage.level)


def update_network_connections(networks: List[HeatNetwork], source_network_name: str, sink_network_name: str,
                               penalty: (float, int) = 0, max_throughput: (float, int) = None, efficiency=1):
    # Update the network connectors first and register the network connections after that

    for i, network in enumerate(networks):
        if network.name == source_network_name:
            source_idx = i
            source_network = network
        elif network.name == sink_network_name:
            sink_idx = i
            sink_network = network

    connected_source_network = {"source": source_network, "penalty": penalty,
                                "max_throughput": max_throughput, "efficiency": efficiency}
    connected_sink_network = {"sink": sink_network, "penalty": penalty,
                              "max_throughput": max_throughput, "efficiency": efficiency}

    # Add the network connections if they don't exist yet or update them.

    if not sink_network.input_connections:
        sink_network.input_connections = [connected_source_network]

    else:
        connected_source_networks_updated = False
        for i, registered_network in enumerate(sink_network.input_connections):
            if registered_network["source"].name == source_network.name:
                # Update if it exists, remove if the throughput is 0
                if max_throughput:
                    if max_throughput < 10:
                        sink_network.input_connections.pop(i)
                    else:
                        sink_network.input_connections[i] = connected_source_network
                connected_source_networks_updated = True

        if not connected_source_networks_updated:
            sink_network.input_connections.append(connected_source_network)

    if not source_network.connected_sink_networks:
        source_network.connected_sink_networks = [connected_sink_network]
    else:
        connected_sink_networks_updated = False
        for i, registered_sink_network in enumerate(source_network.connected_sink_networks):
            if registered_sink_network["sink"].name == sink_network.name:
                if max_throughput:
                    if max_throughput < 10:
                        source_network.connected_sink_networks.pop(i)
                    else:
                        source_network.connected_sink_networks[i] = connected_sink_network
                connected_sink_networks_updated = True

        if not connected_sink_networks_updated:
            source_network.connected_sink_networks.append(connected_sink_network)

    networks[sink_idx] = sink_network
    networks[source_idx] = source_network
    return networks
