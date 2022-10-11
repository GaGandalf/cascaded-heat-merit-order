import unittest
from copy import copy
from datetime import datetime

from dhs import DHS
from energy_converters import HeatSource, HeatDemand, Cooler
from factory import Factory
from location import Location
from network_connectors import HeatPump
from networks import HeatNetwork
from utils import celsius_to_kelvin, load_reference


class TestCooling(unittest.TestCase):

    def test_time_variant_cooling_cost(self):
        testing_factory = init_cooler_testfactory()
        testing_factory.merit_order()
        self.assertEqual(testing_factory.mo[0].name_source, 'Testing Waste Heat Source')

    def test_globals_temperature_reference(self):
        load_reference("data/price_reference_test.csv")
        testing_factory = init_cooler_testfactory()
        testing_factory.merit_order(timestamp=datetime(year=2018, month=1, day=1, hour=16))
        price_warm_day = copy(testing_factory.mo[1].price)
        testing_factory.merit_order(timestamp=datetime(year=2018, month=1, day=1, hour=1))
        price_cold_day = copy(testing_factory.mo[1].price)
        self.assertGreater(price_cold_day, price_warm_day)


def init_cooler_testfactory():
    cn_name = "Texting CN Network"
    ih_name = "Testing IH Network"
    rh_name = "Testing RH Network"
    heat_price = 0

    waste_heat_source_cn = [HeatSource(name="Testing Cooling Heat Source", heat_supply=100, price=0)]
    waste_heat_sources_rh = [HeatSource(name="Testing Waste Heat Source", heat_supply=200, price=heat_price)]
    demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=heat_price)]

    cn_coolers = [Cooler(name="Test Cooler", cooling_capacity=1000, ambient=True, efficiency=0.5)]

    heat_pumps = [HeatPump(name="IH to RH testing Heat Pump",
                           heat_sink=ih_name,
                           heat_source=rh_name
                           ),
                  HeatPump(name="CN to RH testing Heat Pump",
                           heat_sink=rh_name,
                           heat_source=cn_name)
                  ]

    networks = [
        HeatNetwork(name=ih_name, operating_temperature=celsius_to_kelvin(100),
                    heat_demands=demand_systems_ih),
        HeatNetwork(
            name=rh_name, operating_temperature=celsius_to_kelvin(80), heat_sources=waste_heat_sources_rh
        ),
        HeatNetwork(
            name=cn_name, operating_temperature=celsius_to_kelvin(8), heat_sources=waste_heat_source_cn,
            is_cooling_network=True,
            coolers=cn_coolers
        )
    ]

    dhs_location = Location("testlocation", 12, 13)
    factory_location = Location("factoryTestLocation", 12.01, 13.02)

    testing_dhs = DHS(name="TestDHS", location=dhs_location)
    testing_factory = Factory(name="Testfactory", location=factory_location,
                              dhs=testing_dhs, networks=networks,
                              network_connectors=heat_pumps
                              )
    testing_factory.register_network_connections()
    return testing_factory
