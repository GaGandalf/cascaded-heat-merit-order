import unittest
from datetime import datetime

from dhs import DHS
from energy_converters import HeatSource, HeatDemand, Boiler, CHP
from factory import Factory
from location import Location
from merits import Merit
from network_connectors import HeatPump, HeatExchanger
from networks import HeatNetwork, apply_specific_electricity_costs
from utils import find_electricity_price, celsius_to_kelvin


class TestComplexFactory(unittest.TestCase):
    def test_complex_factory(self):
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

        cn1_name = "Cooling Network 1"
        cn2_name = "Cooling Network 2"
        rh_name = "RH Network"
        ih_ht_name = "IH HT Network"
        ih_lt_name = "IH LT Network"

        heat_sources_cn1 = [HeatSource(name="Cooling Demand 1", heat_supply=1500)]
        heat_sources_cn2 = [HeatSource(name="Cooling Demand 2", heat_supply=1000)]
        heat_sources_rh = []
        heat_sources_ih_ht = [Boiler(name="Boiler IH HT", heat_supply=1200, efficiency=0.9),
                              HeatSource(name="Waste Heat IH HT", heat_supply=500)]
        heat_sources_ih_lt = [CHP(name="CHP 1", heat_supply=1000, electrical_efficiency=0.4, thermal_efficiency=0.5)]

        heat_demand_rh = [HeatDemand(name="Heat Demand RH", heat_demand=750)]
        heat_demand_ih_ht = [HeatDemand(name="Heat Demand IH HT", heat_demand=1000)]
        heat_demand_ih_lt = [HeatDemand(name="Heat Demand IH LT", heat_demand=300)]

        networks = [
            HeatNetwork(name=cn1_name, operating_temperature=celsius_to_kelvin(20), heat_sources=heat_sources_cn1,
                        is_cooling_network=True, cooling_cost=6),
            HeatNetwork(name=cn2_name, operating_temperature=celsius_to_kelvin(8), heat_sources=heat_sources_cn2,
                        is_cooling_network=True, cooling_cost=35),
            HeatNetwork(name=rh_name, operating_temperature=celsius_to_kelvin(60), heat_sources=heat_sources_rh,
                        heat_demands=heat_demand_rh),
            HeatNetwork(name=ih_ht_name, operating_temperature=celsius_to_kelvin(120), heat_sources=heat_sources_ih_ht,
                        heat_demands=heat_demand_ih_ht),
            HeatNetwork(name=ih_lt_name, operating_temperature=celsius_to_kelvin(100), heat_sources=heat_sources_ih_lt,
                        heat_demands=heat_demand_ih_lt)
        ]

        network_connectors = [
            HeatPump(name="CN1 to RH HeatPump",
                     max_throughput=2000,
                     efficiency=0.6,
                     heat_sink=rh_name,
                     heat_source=cn1_name),
            HeatPump(name="CN2 to CN1 HeatPump",
                     max_throughput=2000,
                     efficiency=0.4,
                     heat_sink=cn1_name,
                     heat_source=cn2_name),
            HeatPump(name="CN2 to RH HeatPump",
                     max_throughput=500,
                     efficiency=0.6,
                     heat_sink=rh_name,
                     heat_source=cn2_name),
            HeatExchanger(name="IH HT to RH HeatExchanger",
                          max_throughput=500,
                          efficiency=0.95,
                          heat_sink=rh_name,
                          heat_source=ih_ht_name),
            HeatExchanger(name="IH LT to RH HeatExchanger",
                          max_throughput=500,
                          efficiency=0.98,
                          heat_sink=rh_name,
                          heat_source=ih_lt_name),
        ]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="Test DHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks,
                                  network_connectors=network_connectors
                                  )

        testing_factory.connect_dhs(rh_name)
        testing_factory.save_connections = True
        testing_factory.merit_order()

        expected_merits = [
            Merit(
                name_source="Cooling Demand 2",
                name_sink="Heat Demand RH",
                supply=750.0,
                original_supply=566.9254310641492,
                price=-26.407700231277403
            ),
            Merit(
                name_source="Cooling Demand 2",
                name_sink="Test DHS",
                supply=859.3879606676228,
                original_supply=433.07456893585083,
                price=-17.5384668208516
            ),
            Merit(
                name_source="Cooling Demand 1",
                name_sink="Test DHS",
                supply=1120.0526692439878,
                original_supply=622.1944170388671,
                price=-2.7755575615628914e-17
            ),
            Merit(
                name_source="CHP 1",
                name_sink="Heat Demand IH LT",
                supply=300,
                original_supply=300.0,
                price=-2.7755575615628914e-17
            ),
            Merit(
                name_source="Waste Heat IH HT",
                name_sink="Heat Demand IH HT",
                supply=500,
                original_supply=500,
                price=0
            ),
            Merit(
                name_source="CHP 1",
                name_sink="Test DHS",
                supply=750.0,
                original_supply=510.2040816326531,
                price=0.06666666666666665
            ),
            Merit(
                name_source="Boiler IH HT",
                name_sink="Heat Demand IH HT",
                supply=500,
                original_supply=500,
                price=0.08888888888888889
            ),
            Merit(
                name_source="Boiler IH HT",
                name_sink="Test DHS",
                supply=750.0,
                original_supply=526.3157894736843,
                price=0.1290448343079922
            ),
        ]

        self.assertEqual(testing_factory.mo, expected_merits)
