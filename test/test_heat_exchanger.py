import unittest

from dhs import DHS
from energy_converters import HeatSource, HeatDemand
from factory import Factory
from location import Location
from merits import Merit
from network_connectors import NetworkConnector, HeatExchanger
from networks import HeatNetwork


class TestHeatExchanger(unittest.TestCase):
    def testNetworkConnection(self):
        """
        Test if supply units which are connected to a demand via heat-exchanger are correctly registered and
        demands are correctly supplied.
        """
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
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=300,
            original_supply=300.0,
            price=0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=100,
            original_supply=100.0,
            price=0
        )

        self.assertEqual(testing_factory.mo,
                         [expected_1st_merit
                             ,
                          expected_2nd_merit

                          ]
                         )

    def testNetworkConnectionWithEfficiency(self):
        """
                Test if supply units which are connected to a demand via heat-exchanger are correctly registered and
                demands are correctly supplied.
                """
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source", heat_supply=400)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=0)]

        heat_exchanger_from_ih_to_rh = [HeatExchanger(name="IH to RH testing Heat Exchanger",
                                                      heat_sink=rh_name,
                                                      heat_source=ih_name,
                                                      efficiency=0.8
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
                                  network_connectors=heat_exchanger_from_ih_to_rh
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=300,
            original_supply=300.0,
            price=0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=80.0,
            original_supply=100.0,
            price=0
        )

        self.assertEqual(testing_factory.mo,
                         [expected_1st_merit
                             ,
                          expected_2nd_merit

                          ]
                         )

    def testNetworkConnectionWithSerialHeatExchangers(self):
        steam_name = "Testing Steam Network"
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"

        waste_heat_sources_steam = [HeatSource(name="Testing Waste Heat Source", heat_supply=5000)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=400, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=0)]

        heat_exchangers = [HeatExchanger(name="IH to RH testing Heat Exchanger",
                                         heat_sink=rh_name,
                                         heat_source=ih_name,
                                         efficiency=0.8
                                         ),
                           HeatExchanger(name="Steam to IH testing Heat Exchanger",
                                         heat_sink=ih_name,
                                         heat_source=steam_name,
                                         efficiency=0.1
                                         )
                           ]

        networks = [
            HeatNetwork(name=steam_name, operating_temperature=150,
                        heat_sources=waste_heat_sources_steam),
            HeatNetwork(name=ih_name, operating_temperature=100,
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
                                  network_connectors=heat_exchangers
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=400,
            original_supply=4000.0,
            price=0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=80.0,
            original_supply=1000.0,
            price=0
        )

        self.assertEqual(testing_factory.mo, [expected_1st_merit, expected_2nd_merit])

    def testHeatExchangerWithPricing(self):
        """
        As we run with below 100% efficiency in the heat-exchanger, costs rise by a factor of 1/eff
        """
        steam_name = "Testing Steam Network"
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"

        heat_sources_steam = [HeatSource(name="Testing Waste Heat Source Steam", heat_supply=1000, price=1)]
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source", heat_supply=200, price=1)]

        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=0)]

        heat_exchanger_from_ih_to_rh = [HeatExchanger(name="IH to RH testing Heat Exchanger",
                                                      heat_sink=rh_name,
                                                      heat_source=ih_name,
                                                      efficiency=0.1
                                                      ),
                                        HeatExchanger(name="Steam to IH testing Heat Exchanger",
                                                      heat_sink=ih_name,
                                                      heat_source=steam_name,
                                                      efficiency=0.1
                                                      )
                                        ]

        networks = [
            HeatNetwork(name=steam_name, operating_temperature=150, heat_sources=heat_sources_steam),
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_sources=waste_heat_sources_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80,
                heat_demands=demand_systems_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=heat_exchanger_from_ih_to_rh
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=20.0,
            original_supply=200,
            price=10.0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source Steam",
            name_sink="RH Testing Demand",
            supply=10.0,
            original_supply=1000,
            price=100.0
        )

        self.assertEqual(testing_factory.mo,
                         [expected_1st_merit
                             ,
                          expected_2nd_merit

                          ]
                         )

    def testHeatExchangerThroughputLimit(self):
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source", heat_supply=800)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=500, price=0)]

        limited_heat_exchanger = [HeatExchanger(name="HeatExchanger with Throughput Limit",
                                                heat_sink=rh_name,
                                                heat_source=ih_name,
                                                max_throughput=200
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
                                  network_connectors=limited_heat_exchanger
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=300,
            original_supply=300.0,
            price=0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=200,
            original_supply=200.0,
            price=0
        )

        self.assertEqual(testing_factory.mo,
                         [expected_1st_merit
                             ,
                          expected_2nd_merit

                          ]
                         )

    def testHeatExchangerThroughputLimitWithEfficiency(self):
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source", heat_supply=800)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=500, price=0)]

        limited_heat_exchanger = [HeatExchanger(name="HeatExchanger with Throughput Limit",
                                                heat_sink=rh_name,
                                                heat_source=ih_name,
                                                max_throughput=200,
                                                efficiency=0.5
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
                                  network_connectors=limited_heat_exchanger
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=300,
            original_supply=300.0,
            price=0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=200.0,
            original_supply=400.0,
            price=0
        )

        self.assertEqual(testing_factory.mo,
                         [expected_1st_merit
                             ,
                          expected_2nd_merit

                          ]
                         )

    def testSerialHExLimitWithEfficiency(self):
        steam_name = "Testing Steam Network"
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"

        waste_heat_sources_steam = [HeatSource(name="Testing Waste Heat Source", heat_supply=5000)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=400, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=0)]

        heat_exchangers = [HeatExchanger(name="IH to RH testing Heat Exchanger",
                                         heat_sink=rh_name,
                                         heat_source=ih_name,
                                         efficiency=0.8,
                                         max_throughput=50
                                         ),
                           HeatExchanger(name="Steam to IH testing Heat Exchanger",
                                         heat_sink=ih_name,
                                         heat_source=steam_name,
                                         efficiency=0.1
                                         )
                           ]

        networks = [
            HeatNetwork(name=steam_name, operating_temperature=150,
                        heat_sources=waste_heat_sources_steam),
            HeatNetwork(name=ih_name, operating_temperature=100,
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
                                  network_connectors=heat_exchangers
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=400,
            original_supply=4000.0,
            price=0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=50.0,
            original_supply=625.0,
            price=0
        )

        self.assertEqual(testing_factory.mo, [expected_1st_merit, expected_2nd_merit])

    def testSerialHExPricingWithEfficiency(self):
        steam_name = "Testing Steam Network"
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"

        waste_heat_sources_steam = [HeatSource(name="Testing Waste Heat Source", heat_supply=5000, price=100)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=400, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=0)]

        heat_exchangers = [HeatExchanger(name="IH to RH testing Heat Exchanger",
                                         heat_sink=rh_name,
                                         heat_source=ih_name,
                                         efficiency=0.8
                                         ),
                           HeatExchanger(name="Steam to IH testing Heat Exchanger",
                                         heat_sink=ih_name,
                                         heat_source=steam_name,
                                         efficiency=0.1
                                         )
                           ]

        networks = [
            HeatNetwork(name=steam_name, operating_temperature=150,
                        heat_sources=waste_heat_sources_steam),
            HeatNetwork(name=ih_name, operating_temperature=100,
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
                                  network_connectors=heat_exchangers
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=400,
            original_supply=4000.0,
            price=1000.0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=80.0,
            original_supply=1000.0,
            price=1250.0
        )

        self.assertEqual(testing_factory.mo, [expected_1st_merit, expected_2nd_merit])

        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=400, price=100)]
        networks = [
            HeatNetwork(name=steam_name, operating_temperature=150,
                        heat_sources=waste_heat_sources_steam),
            HeatNetwork(name=ih_name, operating_temperature=100,
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
                                  network_connectors=heat_exchangers
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=400,
            original_supply=4000.0,
            price=1100.0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=80.0,
            original_supply=1000.0,
            price=1250.0
        )

        self.assertEqual(testing_factory.mo, [expected_1st_merit, expected_2nd_merit])

    def testSerialHexPricingWithEfficiencyAndLimit(self):
        steam_name = "Testing Steam Network"
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"

        waste_heat_sources_steam = [HeatSource(name="Testing Waste Heat Source", heat_supply=5000, price=100)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=400, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=100)]

        heat_exchangers = [HeatExchanger(name="IH to RH testing Heat Exchanger",
                                         heat_sink=rh_name,
                                         heat_source=ih_name,
                                         efficiency=0.8,
                                         max_throughput=50
                                         ),
                           HeatExchanger(name="Steam to IH testing Heat Exchanger",
                                         heat_sink=ih_name,
                                         heat_source=steam_name,
                                         efficiency=0.1
                                         )
                           ]

        networks = [
            HeatNetwork(name=steam_name, operating_temperature=150,
                        heat_sources=waste_heat_sources_steam),
            HeatNetwork(name=ih_name, operating_temperature=100,
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
                                  network_connectors=heat_exchangers
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=400,
            original_supply=4000.0,
            price=1000.0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=50.0,
            original_supply=625.0,
            price=1350.0
        )

        self.assertEqual(testing_factory.mo, [expected_1st_merit, expected_2nd_merit])

    def testHeatExchangerWithHighEfficiency(self):
        """
        Test if the algorithm can handle efficiencies close to 1 without floating point errors.
        """
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        waste_heat_sources_ih = [HeatSource(name="Testing Waste Heat Source", heat_supply=400)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=0)]
        demand_systems_rh = [HeatDemand(name="RH Testing Demand", heat_demand=100, price=0)]

        heat_exchanger_from_ih_to_rh = [HeatExchanger(name="IH to RH testing Heat Exchanger",
                                                      heat_sink=rh_name,
                                                      heat_source=ih_name,
                                                      efficiency=0.999
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
                                  network_connectors=heat_exchanger_from_ih_to_rh
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=300,
            original_supply=300.0,
            price=0
        )
        expected_2nd_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="RH Testing Demand",
            supply=99.9,
            original_supply=100.0,
            price=0
        )

        self.assertEqual(testing_factory.mo,
                         [expected_1st_merit
                             ,
                          expected_2nd_merit

                          ]
                         )
