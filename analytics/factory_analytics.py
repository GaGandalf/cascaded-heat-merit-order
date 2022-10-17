import copy
import itertools
import json
from datetime import datetime
from typing import List

from cascaded_heat_merit_order.factory_decoder import factory_dict_to_factory_object
from cascaded_heat_merit_order.network_connectors import HeatExchanger, HeatPump
from cascaded_heat_merit_order import Factory

import logging

from analytics.merit_order_tools import sum_merit_order_cost


def permutate_factory(factory: Factory, max_connectors: int = None, output_name="default.txt", supply_demand_df=None):
    """
    The maximum possible number of network-connectors in a factory with n networks is


    Es ist ziehen ohne zurücklegen, wir ziehen max_connectors aus der Menge aller Permutationen


    Am sinnvollsten sind diejenigen Netzwerkverbindungen,
    die mit minimaler Connectoranzahl die Konnectivität maximieren
    """
    max_connectors = 3



    logging.basicConfig(format='%(message)s', level=logging.DEBUG,
                        handlers=[
                            logging.FileHandler(f"permutation_{factory.name}.log", mode="w"),
                            logging.StreamHandler()
                        ])


    logging.info(f"Network Connector Permutation for {factory.name}\n")
    logging.info("Parameters:")
    logging.info(f"Number of connectors to be added: {max_connectors}")
    logging.info(f"Heat networks in {factory.name}: {len(factory.networks)}")
    logging.info(f"Existing network connections: {len(factory.network_connectors)}")

    factory.networks.sort(key=lambda x: x.operating_temperature)

    possible_connections = []


    for i, network in enumerate(factory.networks):
        if i >= 1:
            idx = i-1
            possible_connections.append((network, factory.networks[idx]))
        if i >= 2:
            idx = i-2
            possible_connections.append((network, factory.networks[idx]))
        if len(factory.networks)-i > 1:
            idx = i+1
            possible_connections.append((network, factory.networks[idx]))
        if len(factory.networks)-i > 2:
            idx = i+2
            possible_connections.append((network, factory.networks[idx]))

    # Aus der Menge aller möglichen Verbindungen entfernen wir zunächst die bereits bestehenden Verbindungen:
    if factory.network_connectors:
        for network_connector in factory.network_connectors:
            for i, possible_connection in enumerate(possible_connections):
                if possible_connection[0].name == network_connector.heat_source:
                    possible_connections.pop(i)

    logging.info(f"Possible connections: {len(possible_connections)}")

    configurations = list(itertools.combinations(possible_connections, max_connectors))

    logging.info(f"Possible combinations: {len(configurations)}\n")

    if supply_demand_df:
        calculation_steps = len(supply_demand_df)
    else:
        calculation_steps = 1

    estimated_runtime = len(configurations) * 0.01 * len(factory.networks) * calculation_steps

    factory.connect_dhs(connection_network_name="RH Heat Network")
    factory.persistent_network_connectors = copy.deepcopy(factory.network_connectors)

    logging.info(f"Estimated runtime: {round(estimated_runtime, 2)}s")
    logging.info(f"Starting at {datetime.now()}\n")

    for i, connector_configuration in enumerate(configurations):
        print(f"Running permutation {i + 1}/{len(configurations)}")
        kpi = run_and_analyze(factory)
        factory.network_connectors = copy.deepcopy(factory.persistent_network_connectors)

    print()
    logging.info(f"Finished at {datetime.now()}")
    return None

def connector_configuration_to_network_connectors(connector_configuration: List):
    network_connectors = []
    for connection in connector_configuration:
        heat_source = connection[0]
        heat_sink = connection[1]
        if heat_source.operating_temperature > heat_sink.operating_temperature:
            network_connectors.append(HeatExchanger(name=f"HEx {heat_source.name} to {heat_sink.name}",
                                                    heat_sink=heat_sink.name, heat_source=heat_source.name))
        else:
            network_connectors.append(HeatPump(name=f"HP {heat_source.name} to {heat_sink.name}",
                                               heat_sink=heat_sink.name,
                                               heat_source=heat_source.name,
                                               efficiency=0.5,
                                               max_throughput=10000
                                               ),)
    return network_connectors


def detailed_analysis(factory: Factory):
    """
    Run the Merit order for a given Factory


    Detailed KPI:

    - Utilization of Supply Systems


    """

    raise NotImplementedError


def hotspot_analysis(factory: Factory):
    raise NotImplementedError


def run_and_analyze(factory: Factory):
    """
    Run the Merit Order for the given Factory in all timestamps for which reference Data
    is available.

    For each time step, calculate KPI  for the resulting Merit Order.

    KPI:


    Internal Metrics:

    Energetic:
    - Remaining internal Demand after MO
    - Remaining cooling demand after MO

    Economic:
    - Internal cost
    - Cooling cost not avoided
    - Cooling cost avoided
    - Cost for electricity
    - Cost for fuels

    Ecological:
    - Internal mean CO2 factor
    - total amount of CO2

    DHS Metrics:
    - Energy amount to DHS
    - Average Price to DHS
    - Percentile Price to DHS
    - Total returns from sales to DHS

    - DHS demand coverage in percent

    Competition with DHS Metrics:
    -


    """



    for timestamp in factory.df.index:
        # Make the required network connectors:
        additional_network_connectors = connector_configuration_to_network_connectors(connector_configuration)
        factory.network_connectors.extend(additional_network_connectors)
        factory.register_network_connections()
        factory.merit_order()
        # factory.print_merit_order()

        # Calculate KPI for the Network Configuration here:

        remaining_internal_demand = factory.remaining_internal_demand(timestamp)
        internal_cost = sum_merit_order_cost(factory.mo)
        print(f"Remaining demand: {remaining_internal_demand}")
        print(f"Internal cost: {internal_cost}")

        remaining_cooling_demand = factory.remaining_cooling_demand()


if __name__ == "__main__":
    with open("../factories/lib/simple_factory.json", "r") as input_file:
        factory_dict = json.load(input_file)

    loaded_factory = factory_dict_to_factory_object(factory_dict)
    mutated_factories = permutate_factory(loaded_factory)