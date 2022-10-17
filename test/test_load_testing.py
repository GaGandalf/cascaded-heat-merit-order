import random
import unittest
import time

import pandas as pd

from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import HeatSource, HeatDemand
from cascaded_heat_merit_order.factory import Factory
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.network_connectors import HeatPump, HeatExchanger
from cascaded_heat_merit_order.networks import HeatNetwork


class TestMeritOrderLoad(unittest.TestCase):
    def test_calculation_times(self):
        import sys
        print(sys.getrecursionlimit())
        sys.setrecursionlimit(2000)


        min_temp = 5
        max_temp = 120
        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        res_df = None

        results = {"n_networks": [], "n_sources": [], "n_demands": [], "time": [], "processing_time": []}
        for n_networks, n_heat_demands, n_heat_sources in zip([2, 2, 2, 2, 4, 4, 4, 4, 8, 8, 8, 8, 16, 16, 16, 16],
                                                              [1, 5, 20, 50, 1, 5, 20, 50, 1, 5, 20, 50, 1, 5, 20, 50],
                                                              [1, 5, 20, 50, 1, 5, 20, 50, 1, 5, 20, 50, 1, 5, 20, 50]):
            networks = []
            temp_steps = (max_temp - min_temp) / n_networks

            for l in range(1, n_networks + 1):
                # For each network, make the heat sources and sinks
                operating_temperature = l * temp_steps + min_temp
                heat_sources = []
                for j in range(1, n_heat_sources + 1):
                    heat_supply = random.randint(0, 1000)
                    heat_sources.append(HeatSource(name=f"net_{l}_supply_{j}", heat_supply=heat_supply))

                heat_demands = []
                for k in range(1, n_heat_demands + 1):
                    heat_demand = random.randint(0, 1000)
                    heat_demands.append(HeatDemand(name=f"net_{l}_demand_{k}", heat_demand=heat_demand))
                networks.append(HeatNetwork(name=f"net_{l}", operating_temperature=operating_temperature,
                                            heat_sources=heat_sources, heat_demands=heat_demands))

            # Connect all networks

            previous_network = None
            network_connectors = []
            for network in networks:
                if not previous_network:
                    previous_network = network
                    continue
                else:
                    network_connectors.append(
                        HeatPump(name=f"hp_{previous_network}_to_{network.name}", heat_sink=network.name,
                                 heat_source=previous_network.name)
                    )
                    previous_network = network

            previous_network = None
            for network in reversed(networks):
                if not previous_network:
                    previous_network = network
                    continue
                else:
                    network_connectors.append(
                        HeatExchanger(name=f"hex_{previous_network}_to_{network.name}",
                                      heat_sink=network.name,
                                      heat_source=previous_network.name)
                    )
                    previous_network = network

            testing_factory = Factory(name="Testfactory", location=factory_location,
                                      dhs=testing_dhs, networks=networks,
                                      network_connectors=network_connectors
                                      )


            print("Building and executing merit order:")
            print(f"Networks: {n_networks}")
            print(f"Heat Sources: {n_heat_sources}")
            print(f"Heat Demands: {n_heat_demands}")
            start_time = time.time()
            start_processing_time = time.process_time()



            testing_factory.register_network_connections()
            testing_factory.merit_order()
            end_time = time.time()
            end_processing_time = time.process_time()
            elapsed_time = end_time - start_time
            elapsed_processing_time = end_processing_time - start_processing_time
            print(f"Elapsed time: {elapsed_time}")
            print(f"Processing time: {elapsed_processing_time}")
            print()

            results["n_networks"].append(n_networks)
            results["n_sources"].append(n_heat_sources)
            results["n_demands"].append(n_heat_demands),
            results["time"].append(elapsed_time)
            results["processing_time"].append(elapsed_processing_time)

        res_df = pd.DataFrame.from_dict(results)
        res_df.to_csv("merit_order_stresstest_results.csv")



