import json
import unittest

from dhs import DHS
from energy_converters import HeatSource, HeatDemand, Boiler
from factory import Factory
from factory_decoder import factory_dict_to_factory_object
from factory_encoder import FactoryEncoder
from location import Location
from network_connectors import NetworkConnector
from networks import HeatNetwork


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

        with open("data/testing_factory.json", "w") as output_file:
            json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)

        with open("data/testing_factory.json", "r") as input_file:
            factory_dict = json.load(input_file)

        loaded_factory = factory_dict_to_factory_object(factory_dict)
        loaded_factory.register_network_connections()
        loaded_factory.merit_order()
        self.assertEqual(loaded_factory.mo, testing_factory.mo)
