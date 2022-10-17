import unittest
from datetime import datetime, timedelta

from cascaded_heat_merit_order.energy_converters import HeatSource, HeatDemand
from cascaded_heat_merit_order.merits import Merit
from cascaded_heat_merit_order.networks import HeatNetwork


class TestMeritOrderSingleNetwork(unittest.TestCase):
    def testBasicMeritOrder(self):
        network_name = "Testing IH Network"
        heat_sources = [HeatSource(name="Testing Waste Heat Source", heat_supply=500)]
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
                                   price=0)]
                         )

    def testMultipleSupplyUnitsMeritOrder(self):
        network_name = "Testing Network with multiple supply units"
        heat_sources = [HeatSource(name="Testing Waste Heat Source", heat_supply=500),
                        HeatSource(name="Testing Waste Heat Source 2", heat_supply=800)]
        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=1300, price=0)]
        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)
        merit_order = network.internal_merit_order()
        self.assertIn(merit_order,
                      [[
                          Merit(name_source="Testing Waste Heat Source", name_sink="Testing Demand",
                                supply=500, price=0),
                          Merit(name_source="Testing Waste Heat Source 2", name_sink="Testing Demand",
                                supply=800, price=0)
                      ],
                          [
                              Merit(name_source="Testing Waste Heat Source 2", name_sink="Testing Demand",
                                    supply=800, price=0),
                              Merit(name_source="Testing Waste Heat Source", name_sink="Testing Demand",
                                    supply=500, price=0)
                          ]]
                      )

    def testMultipleSupplyAndDemandUnitsMeritOrder(self):
        network_name = "Testing Network with multiple supply unit and demand units"
        heat_sources = [HeatSource(name="Testing Waste Heat Source", heat_supply=500),
                        HeatSource(name="Testing Waste Heat Source 2", heat_supply=5000, price=5)]
        demand_systems = [HeatDemand(name="Testing Demand", heat_demand=1300, price=0),
                          HeatDemand(name="Testing Demand 2", heat_demand=1000, price=5)
                          ]
        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)
        merit_order = network.internal_merit_order()
        self.assertEqual(merit_order,
                         [

                             Merit(name_source="Testing Waste Heat Source", name_sink="Testing Demand",
                                   supply=500, price=0),
                             Merit(name_source="Testing Waste Heat Source 2", name_sink="Testing Demand",
                                   supply=800, price=5),
                             Merit(name_source="Testing Waste Heat Source 2", name_sink="Testing Demand 2",
                                   supply=1000, price=10)
                         ])

    def testMeritOrderForMultipleTimeSteps(self):
        network_name = "Testing IH Network"
        datetime_now = datetime.now()
        datetime_15_minutes_ago = datetime_now - timedelta(minutes=15)

        heat_sources = [
            HeatSource(name="Testing Waste Heat Source", heat_supply=[
                {
                    "supply": 1000,
                    "timestamp": datetime_15_minutes_ago
                },
                {
                    "supply": 1000,
                    "timestamp": datetime_now
                }])]

        demand_systems = [HeatDemand(name="Testing Demand",
                                     heat_demand=
                                     [
                                         {
                                             "demand": 500,
                                             "timestamp": datetime_15_minutes_ago
                                         },
                                         {
                                             "demand": 800,
                                             "timestamp": datetime_now
                                         }],
                                     price=0)]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)

        merit_order_15_minutes_ago = network.internal_merit_order(timestamp=datetime_15_minutes_ago)
        merit_order_now = network.internal_merit_order(timestamp=datetime_now)

        self.assertEqual(merit_order_15_minutes_ago,
                         [
                             Merit(name_source="Testing Waste Heat Source", name_sink="Testing Demand",
                                   supply=500, price=0)
                         ]
                         )

        self.assertEqual(merit_order_now,
                         [
                             Merit(name_source="Testing Waste Heat Source", name_sink="Testing Demand",
                                   supply=800, price=0)
                         ])

    def testMeritOrderForMultipleTimeStepsOnAMoreComplexSystem(self):
        network_name = "Testing IH Network"
        datetime_now = datetime.now()
        datetime_15_minutes_ago = datetime_now - timedelta(minutes=15)

        heat_sources = [
            HeatSource(name="Testing Waste Heat Source", heat_supply=[
                {
                    "supply": 200,
                    "timestamp": datetime_15_minutes_ago
                },
                {
                    "supply": 400,
                    "timestamp": datetime_now
                }]),
            HeatSource(name="Expensive Waste Heat Source", heat_supply=[
                {
                    "supply": 800,
                    "timestamp": datetime_15_minutes_ago
                },
                {
                    "supply": 300,
                    "timestamp": datetime_now
                }
            ], price=100)

        ]

        demand_systems = [HeatDemand(name="Testing Demand",
                                     heat_demand=
                                     [
                                         {
                                             "demand": 500,
                                             "timestamp": datetime_15_minutes_ago
                                         },
                                         {
                                             "demand": 800,
                                             "timestamp": datetime_now
                                         }
                                     ],
                                     price=0),
                          HeatDemand(name="Cheap Demand",
                                     heat_demand=
                                     [
                                         {
                                             "demand": 100,
                                             "timestamp": datetime_15_minutes_ago
                                         }
                                     ],
                                     price=-20.20)

                          ]

        network = HeatNetwork(name=network_name, operating_temperature=100,
                              heat_sources=heat_sources,
                              heat_demands=demand_systems)

        merit_order_15_minutes_ago = network.internal_merit_order(timestamp=datetime_15_minutes_ago)
        merit_order_now = network.internal_merit_order(timestamp=datetime_now)

        self.assertEqual(merit_order_15_minutes_ago,
                         [
                             Merit(name_source="Testing Waste Heat Source", name_sink="Cheap Demand",
                                   supply=100, price=-20.20),
                             Merit(name_source="Testing Waste Heat Source", name_sink="Testing Demand",
                                   supply=100, price=0),
                             Merit(name_source="Expensive Waste Heat Source", name_sink="Testing Demand",
                                   supply=400, price=100)
                         ]
                         )

        self.assertEqual(merit_order_now,
                         [
                             Merit(name_source="Testing Waste Heat Source", name_sink="Testing Demand",
                                   supply=400, price=0),
                             Merit(name_source="Expensive Waste Heat Source", name_sink="Testing Demand",
                                   supply=300, price=100)
                         ])