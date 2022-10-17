import json
import unittest

import pandas as pd

from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import HeatSource, HeatDemand, Boiler
from cascaded_heat_merit_order.factory import Factory
from cascaded_heat_merit_order.factory_decoder import factory_dict_to_factory_object
from cascaded_heat_merit_order.factory_encoder import FactoryEncoder
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.network_connectors import NetworkConnector
from cascaded_heat_merit_order.networks import HeatNetwork


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
            #loaded_factory.print_merit_order()
            testing_factory.merit_order(timestamp)

            self.assertEqual(testing_factory.mo, loaded_factory.mo)
