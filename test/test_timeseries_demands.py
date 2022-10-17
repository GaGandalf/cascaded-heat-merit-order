import unittest

import pandas as pd

from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order.energy_converters import Boiler, HeatDemand, HeatSource
from cascaded_heat_merit_order.factory import Factory
from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.networks import HeatNetwork
from cascaded_heat_merit_order.utils import celsius_to_kelvin


class TestTimeSeriesMeritOrder(unittest.TestCase):
    def setUp(self) -> None:
        """
        Load the timeseries Data

        :return:
        """
        self.supply_demand_df = pd.read_csv('data/SupplyDemandTestData.csv', sep=";", index_col=0, parse_dates=True,
                                            header=0)

    def test_simple_timeseries_merit_order(self):
        ih_name = "IH Test Network"
        boiler1_name = "Boiler1"
        demand1_name = "Demand1"

        heat_sources_ih = [Boiler(name=boiler1_name, heat_supply=self.supply_demand_df[f"heat_{boiler1_name}"])]
        heat_demands_ih = [HeatDemand(name=demand1_name,
                                      heat_demand=self.supply_demand_df[f"heat_{demand1_name}"], price=0)]

        networks = [
            HeatNetwork(name=ih_name, operating_temperature=celsius_to_kelvin(100), heat_sources=heat_sources_ih,
                        heat_demands=heat_demands_ih)]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        testing_dhs = DHS(name="TestDHS", location=dhs_location)
        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=testing_dhs, networks=networks)
        testing_factory.register_network_connections()
        for timestamp in self.supply_demand_df.index:
            testing_factory.merit_order(timestamp)
            testing_factory.print_merit_order()

    def test_dhs_demand(self):
        """
        :return:
        """
        rh_name = "RH Testing Network"
        rh_waste_name = "Solar1"
        rh_demand_name = "Demand1"

        waste_heat_source_rh = [
            HeatSource(name=rh_waste_name, heat_supply=self.supply_demand_df[f"heat_{rh_waste_name}"])]
        heat_demands_rh = [HeatDemand(name="RH Internal Heat Demand",
                                      heat_demand=self.supply_demand_df[f"heat_{rh_demand_name}"])]

        networks = [
            HeatNetwork(name=rh_name, operating_temperature=celsius_to_kelvin(60), heat_sources=waste_heat_source_rh,
                        heat_demands=heat_demands_rh)]

        dhs_location = Location("testlocation", 12, 13)
        factory_location = Location("factoryTestLocation", 12.01, 13.02)

        dhs_demand_name = "Demand2"
        dhs = DHS(name="DHS", location=dhs_location, demand_profile=self.supply_demand_df[f"heat_{dhs_demand_name}"],
                  min_temp=celsius_to_kelvin(100), max_temp=celsius_to_kelvin(120))

        testing_factory = Factory(name="Testfactory", location=factory_location,
                                  dhs=dhs, networks=networks)

        testing_factory.connect_dhs(rh_name)

        for timestamp in self.supply_demand_df.index:
            testing_factory.merit_order(timestamp)

            print(f"Merit order for {timestamp}")
            testing_factory.print_merit_order()
            print()
