import json

from cascaded_heat_merit_order.network_connectors import HeatExchanger
from cascaded_heat_merit_order.dhs import DHS
from cascaded_heat_merit_order import HeatSource, Boiler, CHP, HeatDemand, Cooler
from cascaded_heat_merit_order import Factory
from cascaded_heat_merit_order.factory_encoder import FactoryEncoder
from cascaded_heat_merit_order import Location
from cascaded_heat_merit_order import HeatNetwork
from cascaded_heat_merit_order import celsius_to_kelvin


def save_example_factory():
    """
    Save a simple example factory for demonstration purposes
    """
    cn_name = "Cooling Network"
    ih_name = "IH Heat Network"
    rh_name = "RH Heat Network"

    heat_sources_cn = [HeatSource(name="Cooling Demand 1", heat_supply=1500)]
    heat_sources_rh = [HeatSource(name="Pressurized Air Waste Heat", heat_supply=500)]
    heat_sources_ih = [Boiler(name="Gas Boiler 1", heat_supply=2500, efficiency=0.75),
                       CHP(name="CHP 1", heat_supply=1000, electrical_efficiency=0.4, thermal_efficiency=0.5)]

    heat_demand_ih = [HeatDemand(name="Heat Demand IH", heat_demand=1000)]
    heat_demand_rh = [HeatDemand(name="Heat Demand RH", heat_demand=1500)]

    coolers_cn = [Cooler(name="Compression Cooler CN", cooling_cost=5, cooling_capacity=1000)]


def save_no_network_connector_factory():
    """
    Save a simple example factory for use in the permutation algorithm without any network connectors
    """
    cn_name = "Cooling Network"
    ih_name = "IH Heat Network"
    rh_name = "RH Heat Network"

    heat_sources_cn = [HeatSource(name="Cooling Demand 1", heat_supply=1500)]
    heat_sources_rh = [HeatSource(name="Pressurized Air Waste Heat", heat_supply=500)]
    heat_sources_ih = [Boiler(name="Gas Boiler 1", heat_supply=2500, efficiency=0.75),
                       CHP(name="CHP 1", heat_supply=1000, electrical_efficiency=0.4, thermal_efficiency=0.5)]

    heat_demand_ih = [HeatDemand(name="Heat Demand IH", heat_demand=1000)]
    heat_demand_rh = [HeatDemand(name="Heat Demand RH", heat_demand=1500)]

    coolers_cn = [Cooler(name="Compression Cooler CN", cooling_cost=5, cooling_capacity=1000),
                  Cooler(name="Hybrid Cooler CN", cooling_cost=0.5, cooling_capacity=500)]

    networks = [
        HeatNetwork(name=cn_name, operating_temperature=celsius_to_kelvin(6), is_cooling_network=True,
                    coolers=coolers_cn, heat_sources=heat_sources_cn),
        HeatNetwork(name=ih_name, operating_temperature=celsius_to_kelvin(110), heat_sources=heat_sources_ih,
                    heat_demands=heat_demand_ih),
        HeatNetwork(name=rh_name, operating_temperature=celsius_to_kelvin(60), heat_sources=heat_sources_rh,
                    heat_demands=heat_demand_rh)
    ]

    dhs_location = Location("testlocation", 12, 13)
    factory_location = Location("factoryTestLocation", 12.01, 13.02)

    testing_dhs = DHS(name="TestDHS", location=dhs_location)
    testing_factory = Factory(name="Testfactory", location=factory_location,
                              dhs=testing_dhs, networks=networks)

    with open("lib/no_network_connector_factory.json", "w") as output_file:
        json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)


def save_simple_factory():
    """
    Save a simple example factory for use in the permutation algorithm without any network connectors
    """
    cn_name = "Cooling Network"
    ih_name = "IH Heat Network"
    rh_name = "RH Heat Network"

    heat_sources_cn = [HeatSource(name="Cooling Demand 1", heat_supply=1500)]
    heat_sources_rh = [HeatSource(name="Pressurized Air Waste Heat", heat_supply=500)]
    heat_sources_ih = [Boiler(name="Gas Boiler 1", heat_supply=2500, efficiency=0.75),
                       CHP(name="CHP 1", heat_supply=1000, electrical_efficiency=0.4, thermal_efficiency=0.5)]

    heat_demand_ih = [HeatDemand(name="Heat Demand IH", heat_demand=1000)]
    heat_demand_rh = [HeatDemand(name="Heat Demand RH", heat_demand=1500)]

    coolers_cn = [Cooler(name="Compression Cooler CN", cooling_cost=5, cooling_capacity=1000),
                  Cooler(name="Hybrid Cooler CN", cooling_cost=0.5, cooling_capacity=500)]

    networks = [
        HeatNetwork(name=cn_name, operating_temperature=celsius_to_kelvin(6), is_cooling_network=True,
                    coolers=coolers_cn, heat_sources=heat_sources_cn),
        HeatNetwork(name=ih_name, operating_temperature=celsius_to_kelvin(110), heat_sources=heat_sources_ih,
                    heat_demands=heat_demand_ih),
        HeatNetwork(name=rh_name, operating_temperature=celsius_to_kelvin(60), heat_sources=heat_sources_rh,
                    heat_demands=heat_demand_rh)
    ]

    network_connectors = [
        HeatExchanger(name="IH to RH testing Heat Exchanger",
                         heat_sink=rh_name,
                         heat_source=ih_name
                         )
    ]

    dhs_location = Location("testlocation", 12, 13)
    factory_location = Location("factoryTestLocation", 12.01, 13.02)

    testing_dhs = DHS(name="TestDHS", location=dhs_location)
    testing_factory = Factory(name="Simple Factory", location=factory_location,
                              dhs=testing_dhs, networks=networks, network_connectors=network_connectors)

    testing_factory.register_network_connections()

    with open("lib/simple_factory.json", "w") as output_file:
        json.dump(testing_factory, output_file, cls=FactoryEncoder, indent=6)


if __name__ == "__main__":
    save_simple_factory()
