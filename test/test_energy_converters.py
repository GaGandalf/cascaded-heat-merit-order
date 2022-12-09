import unittest
from datetime import datetime

import pandas as pd

from cascaded_heat_merit_order.energy_converters import Boiler, HeatDemand, CHP
from cascaded_heat_merit_order.fuel import Fuel
from cascaded_heat_merit_order.merits import Merit
from cascaded_heat_merit_order.networks import HeatNetwork


class TestEnergyConverters(unittest.TestCase):
    def testBasicBoiler(self):
        network_name = "Testing IH Network"
        heat_sources = [Boiler(name="Testing Waste Heat Source", heat_supply=500)]
        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=500, price=0)]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)
        most_basic_merit_order = network.internal_merit_order()
        self.assertEqual(most_basic_merit_order,

                         [
                             Merit(name_source="Testing Waste Heat Source",
                                   name_sink="Testing Demand",
                                   supply=500,
                                   price=0.0989)]
                         )

    def testBoilerWithEfficiency(self):
        network_name = "Testing IH Network"
        heat_sources = [Boiler(name="Testing Waste Heat Source", heat_supply=500, efficiency=0.5)]
        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=500, price=0)]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)
        most_basic_merit_order = network.internal_merit_order()
        self.assertEqual(most_basic_merit_order,

                         [
                             Merit(name_source="Testing Waste Heat Source",
                                   name_sink="Testing Demand",
                                   supply=500,
                                   price=0.0989 / 0.5)]
                         )

    def testBoilerWithCustomFuel(self):
        network_name = "Testing IH Network"
        fuel = Fuel(name="Funky Oil", co2_equivalent=666, calorific_value=100)
        heat_sources = [Boiler(name="Testing Waste Heat Source", heat_supply=500, fuel=fuel, efficiency=0.5)]
        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=500, price=0)]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)
        most_basic_merit_order = network.internal_merit_order()
        self.assertEqual(most_basic_merit_order,

                         [
                             Merit(name_source="Testing Waste Heat Source",
                                   name_sink="Testing Demand",
                                   supply=500,
                                   price=0.0989 / 0.5)]
                         )

    def testBoilerWithFuelReferenceInternal(self):
        price_ref = pd.read_csv("data/price_reference_test.csv", sep=";", header=0, index_col=0, parse_dates=True)
        network_name = "Testing IH Network"
        fuel = Fuel(name="Funky Oil", co2_equivalent=666, calorific_value=100)
        boiler_efficiency = 0.5
        heat_sources = [Boiler(name="Testing Boiler", heat_supply=500, fuel=fuel,
                               fuel_price_reference=price_ref.GasPrice, efficiency=boiler_efficiency)]

        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=500, price=0)]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)

        timestamp = datetime(2018, 1, 1, 17, 0)
        network_mo_with_custom_price = network.internal_merit_order(timestamp)


        self.assertEqual(network_mo_with_custom_price,
                         [
                             Merit(name_source="Testing Boiler",
                                   name_sink="Testing Demand",
                                   supply=500,
                                   original_supply=500,
                                   price=0.1978)]
                         )

    def testBoilerWithFuelReferenceMultipleTimesteps(self):
        fuel_ref = pd.read_csv("data/price_reference_test.csv", sep=";", header=0, index_col=0, parse_dates=True)
        network_name = "Testing IH Network"
        fuel = Fuel(name="Funky Oil", co2_equivalent=666, calorific_value=100)
        boiler_efficiency = 0.5
        heat_sources = [Boiler(name="Testing Boiler", heat_supply=500, fuel=fuel,
                               fuel_price_reference=fuel_ref.GasPrice, efficiency=boiler_efficiency)]

        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=500, price=0)]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)

        timestamp1 = datetime(2018, 1, 1, 17, 0)
        network_mo_with_custom_price = network.internal_merit_order(timestamp1)
        self.assertEqual(network_mo_with_custom_price,
                         [
                             Merit(name_source="Testing Boiler",
                                   name_sink="Testing Demand",
                                   supply=500,
                                   original_supply=500,
                                   price=0.1978)]
                         )

        timestamp2 = datetime(2018, 1, 1, 18, 0)
        network_mo_with_custom_price = network.internal_merit_order(timestamp2)
        expected_price = fuel_ref.GasPrice[timestamp2] / boiler_efficiency
        self.assertEqual(network_mo_with_custom_price,
                         [
                             Merit(name_source="Testing Boiler",
                                   name_sink="Testing Demand",
                                   supply=500,
                                   original_supply=500,
                                   price=0.1978)]
                         )

    def testBasicCHP(self):
        network_name = "CHP Network"
        thermal_efficiency = 0.5
        electrical_efficiency = 0.25
        price_ref = pd.read_csv("data/price_reference_test.csv", sep=";", header=0, index_col=0, parse_dates=True)
        heat_sources = [CHP(name="Testing CHP", heat_supply=500,
                            electrical_efficiency=electrical_efficiency,
                            thermal_efficiency=thermal_efficiency,
                            fuel_price_reference=price_ref.GasPrice,
                            electricity_price_reference=price_ref.ElectricityPrice
                            )]

        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=500, price=0)]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)

        timestamp = datetime(2018, 1, 1, 17, 0)
        network_mo_with_custom_price = network.internal_merit_order(timestamp)

        self.assertEqual(network_mo_with_custom_price,
                         [
                             Merit(name_source="Testing CHP",
                                   name_sink="Testing Demand",
                                   supply=500,
                                   original_supply=500,
                                   price=0.06)]
                         )


if __name__ == '__main__':
    unittest.main()
