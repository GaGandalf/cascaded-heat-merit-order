import json
import unittest

import pandas as pd

from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import HeatSource, HeatDemand, Boiler, CHP
from cascaded_heat_merit_order.factory import Factory
from cascaded_heat_merit_order.factory_decoder import factory_dict_to_factory_object
from cascaded_heat_merit_order.factory_encoder import FactoryEncoder
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.network_connectors import NetworkConnector, HeatPump, HeatExchanger
from cascaded_heat_merit_order.networks import HeatNetwork
from cascaded_heat_merit_order.utils import celsius_to_kelvin


class TestFactoryEncoderAndDecoder(unittest.TestCase):
    def test_encoder(self):
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source", heat_supply=500)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=0)]

        ideal_heat_exchanger_from_ih_to_rh = [NetworkConnector(name="IH to RH testing Heat Exchanger",
                                                               heat_sink=rh_name,
                                                               heat_source=ih_name
                                                               )]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_sources=waste_heat_sources_ih,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80,
                heat_demands=demand_systems_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=ideal_heat_exchanger_from_ih_to_rh
                                  )
        testing_factory.register_network_connections()
        with open("data/testing_factory.json", "w") as output_file:
            json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)

    def test_decoder(self):
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source", heat_supply=500),
                                 Boiler(name="Boiler", heat_supply=500, efficiency=0.5)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=0)]

        ideal_heat_exchanger_from_ih_to_rh = [NetworkConnector(name="IH to RH testing Heat Exchanger",
                                                               heat_sink=rh_name,
                                                               heat_source=ih_name
                                                               )]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_sources=waste_heat_sources_ih,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80,
                heat_demands=demand_systems_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=ideal_heat_exchanger_from_ih_to_rh
                                  )

        testing_factory.register_network_connections()
        testing_factory.merit_order()
        testing_factory.reset_networks()

        with open("data/testing_factory.json", "w") as output_file:
            json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)

        with open("data/testing_factory.json", "r") as input_file:
            factory_dict = json.load(input_file)

        loaded_factory = factory_dict_to_factory_object(factory_dict)
        loaded_factory.register_network_connections()
        loaded_factory.merit_order()
        self.assertEqual(loaded_factory.mo, testing_factory.mo)

    def test_encoder_with_reference_df(self):
        reference_df = pd.read_csv("data/SupplyDemandTestDataEncoderReady.csv", sep=";", index_col=0, parse_dates=True,
                                   header=0)

        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source",
                                            heat_supply=reference_df.heat_Testing_Waste_Heat_Source)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=reference_df.heat_IH_Testing_Demand,
                                        price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=reference_df.heat_RH_Testing_Demand,
                                        price=0)]

        ideal_heat_exchanger_from_ih_to_rh = [NetworkConnector(name="IH to RH testing Heat Exchanger",
                                                               heat_sink=rh_name,
                                                               heat_source=ih_name
                                                               )]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_sources=waste_heat_sources_ih,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80,
                heat_demands=demand_systems_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=ideal_heat_exchanger_from_ih_to_rh
                                  )
        testing_factory.register_network_connections()
        with open("data/testing_factory_with_ref_df.json", "w") as output_file:
            json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)

    def test_decoder_with_reference_df(self):
        reference_df = pd.read_csv("data/SupplyDemandTestDataEncoderReady.csv", sep=";", index_col=0, parse_dates=True,
                                   header=0)
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source",
                                            heat_supply=reference_df.heat_Testing_Waste_Heat_Source)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=reference_df.heat_IH_Testing_Demand,
                                        price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=reference_df.heat_RH_Testing_Demand,
                                        price=0)]

        ideal_heat_exchanger_from_ih_to_rh = [NetworkConnector(name="IH to RH testing Heat Exchanger",
                                                               heat_sink=rh_name,
                                                               heat_source=ih_name
                                                               )]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_sources=waste_heat_sources_ih,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80,
                heat_demands=demand_systems_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=ideal_heat_exchanger_from_ih_to_rh
                                  )
        testing_factory.register_network_connections()
        with open("data/testing_factory_with_ref_df.json", "w") as output_file:
            json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)

        with open("data/testing_factory_with_ref_df.json", "r") as input_file:
            factory_dict = json.load(input_file)

        loaded_factory = factory_dict_to_factory_object(factory_dict, reference_df)
        for timestamp in reference_df.index:
            loaded_factory.merit_order(timestamp)
            # loaded_factory.print_merit_order()
            testing_factory.merit_order(timestamp)

            self.assertEqual(testing_factory.mo, loaded_factory.mo)

    def test_encoder_decoder_with_chp(self):
        cn_name = "CN"
        ih_ht_name = "HNHT"
        ih_lt_name = "HNLT"

        heat_sources_cn = [HeatSource(name="Cooling Demand 1", heat_supply=1500)]
        heat_sources_ih_ht = [Boiler(name="Boiler", heat_supply=1200, efficiency=0.9),
                              CHP(name="CHP", heat_supply=1000, electrical_efficiency=0.5, thermal_efficiency=0.4),
                              HeatSource(name="Waste Heat", heat_supply=500)]

        heat_source_hnlt = [HeatSource(name="Dummy Heat Source", heat_supply=0)]
        heat_demand_ih_ht = [HeatDemand(name="Heat Demand HNHT", heat_demand=1000)]
        heat_demand_ih_lt = [HeatDemand(name="Heat Demand HNLT", heat_demand=300)]

        networks = [
            HeatNetwork(name=cn_name, operating_temperature=celsius_to_kelvin(20), heat_sources=heat_sources_cn,
                        is_cooling_network=True, cooling_cost=0),

            HeatNetwork(name=ih_ht_name, operating_temperature=celsius_to_kelvin(100), heat_sources=heat_sources_ih_ht,
                        heat_demands=heat_demand_ih_ht),

            HeatNetwork(name=ih_lt_name, operating_temperature=celsius_to_kelvin(80),
                        heat_demands=heat_demand_ih_lt)
        ]

        network_connectors = [
            HeatPump(name="CN to HNLT HeatPump",
                     max_throughput=2000,
                     efficiency=0.6,
                     heat_sink=ih_lt_name,
                     heat_source=cn_name),
            HeatExchanger(name="HNHT to HNLT HeatExchanger",
                          max_throughput=500,
                          efficiency=0.95,
                          heat_sink=ih_lt_name,
                          heat_source=ih_ht_name),
        ]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)
        testing_factory = Factory(name="Testfactory", location=factory_location
                                  , networks=networks,
                                  network_connectors=network_connectors
                                  )

        with open("testing_factory.json", "w") as output_file:
            json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)

        testing_factory.merit_order()
        testing_factory.print_merit_order()

        with open("testing_factory.json", "r") as input_file:
            factory_dict = json.load(input_file)

        loaded_factory = factory_dict_to_factory_object(factory_dict)
        loaded_factory.register_network_connections()
        loaded_factory.merit_order()

        self.assertEqual(testing_factory.mo, loaded_factory.mo)

    def test_encoder_decoder_with_chp_with_reference(self):
        cn_name = "CN"
        ih_ht_name = "HNHT"
        ih_lt_name = "HNLT"

        reference = pd.read_csv("data/eta_cmo_factory_reference.csv", sep=";", index_col=0, parse_dates=True)

        heat_sources_cn = [HeatSource(name="Cooling Demand 1", heat_supply=reference["heat_Cooling_Demand_1"])]
        heat_sources_ih_ht = [Boiler(name="Boiler", heat_supply=1200, efficiency=0.9),
                              CHP(name="CHP", heat_supply=1000, electrical_efficiency=0.5, thermal_efficiency=0.4),
                              HeatSource(name="Waste Heat", heat_supply=reference["heat_Waste_Heat"])]

        # heat_source_hnlt = [HeatSource(name="Dummy Heat Source", heat_supply=0)]
        heat_demand_ih_ht = [HeatDemand(name="Heat Demand HNHT", heat_demand=reference["heat_Heat_Demand_HNHT"])]
        heat_demand_ih_lt = [HeatDemand(name="Heat Demand HNLT", heat_demand=reference["heat_Heat_Demand_HNLT"])]

        networks = [
            HeatNetwork(name=cn_name, operating_temperature=celsius_to_kelvin(20), heat_sources=heat_sources_cn,
                        is_cooling_network=True, cooling_cost=0),

            HeatNetwork(name=ih_ht_name, operating_temperature=celsius_to_kelvin(100), heat_sources=heat_sources_ih_ht,
                        heat_demands=heat_demand_ih_ht),

            HeatNetwork(name=ih_lt_name, operating_temperature=celsius_to_kelvin(80),
                        heat_demands=heat_demand_ih_lt)
        ]

        network_connectors = [
            HeatPump(name="CN to HNLT HeatPump",
                     max_throughput=2000,
                     efficiency=0.6,
                     heat_sink=ih_lt_name,
                     heat_source=cn_name),
            HeatExchanger(name="HNHT to HNLT HeatExchanger",
                          max_throughput=500,
                          efficiency=0.95,
                          heat_sink=ih_lt_name,
                          heat_source=ih_ht_name),
        ]

        factory_location = Location("factoryTestLocation", 12.01, 13.02)
        testing_factory = Factory(name="Testfactory", location=factory_location
                                  , networks=networks,
                                  network_connectors=network_connectors
                                  )

        with open("testing_factory.json", "w") as output_file:
            json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)

        with open("testing_factory.json", "r") as input_file:
            factory_dict = json.load(input_file)

        loaded_factory = factory_dict_to_factory_object(factory_dict, reference_df=reference)
        loaded_factory.register_network_connections()

        for timestamp in reference.index:
            testing_factory.merit_order(timestamp)
            loaded_factory.merit_order(timestamp)
            self.assertEqual(testing_factory.mo, loaded_factory.mo)
