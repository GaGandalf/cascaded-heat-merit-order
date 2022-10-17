import datetime
import unittest

from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import HeatSource, HeatDemand
from cascaded_heat_merit_order.factory import Factory
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.merits import Merit
from cascaded_heat_merit_order.network_connectors import HeatPump
from cascaded_heat_merit_order.networks import HeatNetwork, apply_specific_electricity_costs
from cascaded_heat_merit_order.utils import find_electricity_price


class TestHeatPump(unittest.TestCase):
    def testNetworkConnection(self):
        """
        Test if supply units which are connected to a demand via heat-exchanger are correctly registered and
        demands are correctly supplied.
        """
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        heat_price = 0
        waste_heat_sources_rh = [HeatSource(name="Testing Waste Heat Source", heat_supply=200, price=heat_price)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=heat_price)]

        ideal_heat_pump_from_rh_to_ih = [HeatPump(name="IH to RH testing Heat Pump",
                                                  heat_sink=ih_name,
                                                  heat_source=rh_name
                                                  )]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80, heat_sources=waste_heat_sources_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=ideal_heat_pump_from_rh_to_ih
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=240,
            original_supply=200,
            price=apply_specific_electricity_costs(5, heat_price,
                                                   find_electricity_price(timestamp=datetime.datetime.now()))
        )

        self.assertEqual(testing_factory.mo, [expected_1st_merit])

    def testHeatPumpWithHeatCosts(self):
        """
        Test if supply units which are connected to a demand via heat-exchanger are correctly registered and
        demands are correctly supplied.
        """
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        heat_price = 100
        waste_heat_sources_rh = [HeatSource(name="Testing Waste Heat Source", heat_supply=200, price=heat_price)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=0)]

        ideal_heat_pump_from_rh_to_ih = [HeatPump(name="IH to RH testing Heat Pump",
                                                  heat_sink=ih_name,
                                                  heat_source=rh_name
                                                  )]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80, heat_sources=waste_heat_sources_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=ideal_heat_pump_from_rh_to_ih
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_price = apply_specific_electricity_costs(5, heat_price,
                                                          find_electricity_price(timestamp=datetime.datetime.now()))
        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=240,
            original_supply=200,
            price=expected_price)

        self.assertEqual(testing_factory.mo, [expected_1st_merit])

    def testHeatPumpWithSupplyAndDemandPrice(self):
        ih_name = "IH"
        rh_name = "RH"

        demand_price = 100
        supply_price = 60

        waste_heat_sources_rh = [HeatSource(name="Testing Waste Heat Source", heat_supply=200, price=supply_price)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=demand_price)]

        ideal_heat_pump_from_rh_to_ih = [HeatPump(name="IH to RH testing Heat Pump",
                                                  heat_sink=ih_name,
                                                  heat_source=rh_name
                                                  )]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80, heat_sources=waste_heat_sources_rh
            )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=ideal_heat_pump_from_rh_to_ih
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_supply_price = apply_specific_electricity_costs(5, supply_price,
                                                                 find_electricity_price(
                                                                     timestamp=datetime.datetime.now()))
        expected_price = expected_supply_price + demand_price

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=240,
            original_supply=200,
            price=expected_price)

        self.assertEqual(testing_factory.mo, [expected_1st_merit])

    def testSerialHeatPump(self):
        cn_name = "Texting CN Network"
        ih_name = "Testing IH Network"
        rh_name = "Testing RH Network"
        heat_price = 0

        waste_heat_source_cn = [HeatSource(name="Testing Cooling Heat Source", heat_supply=100, price=0)]
        waste_heat_sources_rh = [HeatSource(name="Testing Waste Heat Source", heat_supply=200, price=heat_price)]
        demand_systems_ih = [HeatDemand(name="IH Testing Demand", heat_demand=300, price=heat_price)]

        heat_pumps = [HeatPump(name="IH to RH testing Heat Pump",
                               heat_sink=ih_name,
                               heat_source=rh_name
                               ),
                      HeatPump(name="CN to RH testing Heat Pump",
                               heat_sink=rh_name,
                               heat_source=cn_name)
                      ]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=100,
                        heat_demands=demand_systems_ih),
            HeatNetwork(
                name=rh_name, operating_temperature=80, heat_sources=waste_heat_sources_rh
            ),
            HeatNetwork(
                name=cn_name, operating_temperature=72, heat_sources=waste_heat_source_cn
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
        testing_factory.merit_order()

        expected_1st_merit = Merit(
            name_source="Testing Waste Heat Source",
            name_sink="IH Testing Demand",
            supply=240.0,
            original_supply=200,
            price=apply_specific_electricity_costs(5, heat_price,
                                                   find_electricity_price(timestamp=datetime.datetime.now()))
        )

        expected_1st_price = apply_specific_electricity_costs(5, 0,
                                                              find_electricity_price(timestamp=datetime.datetime.now()))

        expected_2nd_price = apply_specific_electricity_costs(10, expected_1st_price, find_electricity_price(
            timestamp=datetime.datetime.now()))


        expected_2nd_merit = Merit(
            name_source="Testing Cooling Heat Source",
            name_sink="IH Testing Demand",
            supply=60.0,
            original_supply=45.45454545454545,
            price=expected_2nd_price
        )

        self.assertEqual(testing_factory.mo, [expected_1st_merit, expected_2nd_merit])

    def testHeatPumpWithThroughPutLimit(self):
        """
        Two Heat Networks are connected via a throughput limited Heat-Pump.

        In the low temperature network, a heat-source offers more heat than what can be transferred.
        In the high temperature network, a heat-demand requests the amount of heat that can be offered by the lt-source.
        The specific price of both heat-source and heat-demand is 0.


        Expected Behaviour:
        - The lt-source supplies the limit to the ht-demand.
        - The merit price consists of the electricity price for the heat-pump.

        - The lt-source is reduced by the supplied amount minus the supplied heat via electricity in the heat-pump
        """
        lt_name = "LT Testing Network"
        ht_name = "HT Testing Network"

        lt_source_supply = 1000

        heat_source_lt = [HeatSource(name="Testing Heat Source", heat_supply=lt_source_supply, price=0)]
        heat_demand_ht = [HeatDemand(name="Testing Heat Demand", heat_demand=500, price=0)]

        networks = [
            HeatNetwork(name=ht_name, operating_temperature=160, heat_demands=heat_demand_ht),
            HeatNetwork(name=lt_name, operating_temperature=120, heat_sources=heat_source_lt)
        ]

        heatpump_limit = 250

        limited_heatpump_lt_to_ht = [HeatPump(name="LT to HT testing heat pump",
                                              heat_sink=ht_name,
                                              heat_source=lt_name,
                                              max_throughput=heatpump_limit)]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=limited_heatpump_lt_to_ht
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_price = apply_specific_electricity_costs(4, 0,
                                                          find_electricity_price(timestamp=datetime.datetime.now()))

        expected_merit = Merit(
            name_source="Testing Heat Source",
            name_sink="Testing Heat Demand",
            supply=250.0,
            original_supply=200.0,
            price=expected_price
        )

        self.assertEqual(testing_factory.mo, [expected_merit])

        testing_factory.merit_order()
        self.assertEqual(testing_factory.mo, [expected_merit])

    def testSerialHeatPumpWithThroughPutLimit(self):
        """
        Three networks are connected via two throughput-limited heat-pumps.
        The limit of both heat-pumps is 400kW

        In the low temperature network, a heat-source offers 1000kW of heat.
        In the medium temperature network, a heat-demand requests 240kW of heat.
        In the high temperature network, a heat-demand requests 500kW of heat.

        The LT-MT HeatPump has a COP of 4.
        The MT-HT HeatPump has a COP of 4.

        Expected Behaviour:
        - The lt source fully supplies the medium temperature demand first
        - The lt - mt heatpump limit is reduced by 200kW

        - The lt source can supplies 250 + 250/4 = 312.5kW to the high temperature demand
        :return:
        """

        lt_name = "LT Testing Network"
        mt_name = "MT Testing Network"
        ht_name = "HT Testing Network"

        lt_source_supply = 1000

        heat_source_lt = [HeatSource(name="Testing Heat Source", heat_supply=lt_source_supply, price=0)]
        heat_demand_mt = [HeatDemand(name="Testing MT Heat Demand", heat_demand=250, price=0)]
        heat_demand_ht = [HeatDemand(name="Testing Heat Demand", heat_demand=500, price=0)]

        networks = [
            HeatNetwork(name=ht_name, operating_temperature=213.333333333, heat_demands=heat_demand_ht),
            HeatNetwork(name=lt_name, operating_temperature=120, heat_sources=heat_source_lt),
            HeatNetwork(name=mt_name, operating_temperature=160, heat_demands=heat_demand_mt)
        ]

        heatpump_limit = 400

        heat_pumps = [HeatPump(name="LT to MT testing heat pump",
                               heat_sink=mt_name,
                               heat_source=lt_name,
                               max_throughput=heatpump_limit),
                      HeatPump(name="MT to HT testing heat pump",
                               heat_sink=ht_name,
                               heat_source=mt_name,
                               max_throughput=heatpump_limit
                               )]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=heat_pumps
                                  )
        testing_factory.register_network_connections()
        testing_factory.merit_order()

        expected_1st_price = apply_specific_electricity_costs(4, 0,
                                                              find_electricity_price(timestamp=datetime.datetime.now()))

        expected_2nd_price = apply_specific_electricity_costs(4, expected_1st_price, find_electricity_price(
            timestamp=datetime.datetime.now()))

        expected_merits = [
            Merit(
                name_source="Testing Heat Source",
                name_sink="Testing MT Heat Demand",
                supply=250.0,
                original_supply=200.0,
                price=expected_1st_price
            ),
            Merit(
                name_source="Testing Heat Source",
                name_sink="Testing Heat Demand",
                supply=187.5,
                original_supply=120.0,
                price=expected_2nd_price
            )
        ]

        self.assertEqual(testing_factory.mo, expected_merits)