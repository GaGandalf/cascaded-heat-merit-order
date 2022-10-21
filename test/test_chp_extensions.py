import unittest

import pandas as pd

from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import CHP, HeatDemand, HeatSource
from cascaded_heat_merit_order.factory import Factory
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.merits import Merit
from cascaded_heat_merit_order.networks import HeatNetwork
from cascaded_heat_merit_order.utils import celsius_to_kelvin


class TestCoupledCHP(unittest.TestCase):
    def testCoupledCHPSolo(self):
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        heat_sources_ih = [CHP(name="CHP", heat_supply=1000, coupled_supply=True,
                               supply_split=(0.4, 0.6), coupled_network=rh_name, coupling_waste_cost=0.1)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=500, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=800, price=0)]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=celsius_to_kelvin(100),
                        heat_sources=heat_sources_ih,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=celsius_to_kelvin(80),
                heat_demands=demand_systems_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks)
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="CHP",
            name_sink="IH Testing Demand",
            supply=400,
            original_supply=400.0,
            price=-0.020000000000000004
        )
        expected_2nd_merit = Merit(
            name_source="Coupled Supply CHP 0",
            name_sink="RH Testing Demand",
            supply=600,
            original_supply=600,
            price=-0.1
        )
        self.assertEqual(testing_factory.mo,  [expected_1st_merit, expected_2nd_merit])


    def testCoupledCHPWithCompetingHeatSource(self):
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        heat_sources_ih = [CHP(name="CHP", heat_supply=1000, coupled_supply=True,
                               supply_split=(0.4, 0.6), coupled_network=rh_name, coupling_waste_cost=0.01)]
        heat_sources_rh = [HeatSource(name="Cheap Waste Heat", heat_supply=200, price=-0.05)]

        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=500, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=700, price=0)]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=celsius_to_kelvin(100),
                        heat_sources=heat_sources_ih,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=celsius_to_kelvin(80),
                heat_demands=demand_systems_rh, heat_sources=heat_sources_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks)
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="CHP",
            name_sink="IH Testing Demand",
            supply=400,
            original_supply=400.0,
            price=-0.11000000000000001
        )
        expected_2nd_merit = Merit(
            name_source="Cheap Waste Heat",
            name_sink="RH Testing Demand",
            supply=200,
            original_supply=200.0,
            price=-0.05
        )
        expected_3rd_merit = Merit(
            name_source="Coupled Supply CHP 0",
            name_sink="RH Testing Demand",
            supply=500,
            original_supply=500.0,
            price=-0.01
        )
        self.assertEqual(testing_factory.mo, [expected_1st_merit, expected_2nd_merit, expected_3rd_merit])


class TestMinimumSupplyCHP(unittest.TestCase):
    def testMinimumSupplyCHP(self):
        network_name = "CHP Network"
        thermal_efficiency = 0.5
        electrical_efficiency = 0.25
        heat_sources = [CHP(name="Testing CHP", heat_supply=500,
                            electrical_efficiency=electrical_efficiency,
                            thermal_efficiency=thermal_efficiency,
                            minimum_supply=400
                            )]

        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=500, price=0)]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)

        network_mo = network.internal_merit_order()

        self.assertEqual(network_mo,
                         [
                             Merit(name_source="Testing CHP",
                                   name_sink="Testing Demand",
                                   supply=500,
                                   original_supply=500,
                                   price=0)]
                         )