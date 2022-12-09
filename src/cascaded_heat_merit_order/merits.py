class Merit:
    def __init__(self, name_source: str, name_sink: str, supply: float, price: float, primary_energy_factor: float=1, co2_intensity=0, original_supply=None,
                 connections=None, sink_internal=True, source_internal=True, supply_is_coupled=False, el_factor=0, eff_in = 1, name_source_net=None, name_sink_net=None
                 ) -> object:
        self.name_source = name_source
        self.name_sink = name_sink
        self.supply = supply
        self.price = price
        self.connections = connections
        self.co2_intensity = co2_intensity
        self.sink_internal = sink_internal
        self.source_internal = source_internal
        self.supply_is_coupled = supply_is_coupled
        self.primary_energy_factor = primary_energy_factor
        self.electricity_production_factor = el_factor
        self.efficiency_in = eff_in
        self.name_source_network = name_source_net
        self.name_sink_network = name_sink_net

        if not original_supply:
            self.original_supply = supply
        else:
            self.original_supply = original_supply

    def __eq__(self, other):
        return self.name_source == other.name_source and self.name_sink == other.name_sink and \
               self.supply == other.supply and self.price == other.price

    def __str__(self):
        return f"{self.name_source} supplies {self.supply} to {self.name_sink} @ {self.price} €/MWh"


class DemandMerit:
    def __init__(self, name: str, demand: float, price: float, network: str):
        self.name = name
        self.demand = demand
        self.price = price
        self.network = network

    def __str__(self):
        return f"{self.name} demands {self.demand} @ {self.price} €/kWh"


class SupplyMerit:
    def __init__(self, name: str, supply: float, price: float, network: str, co2_equivalent=0, connections=None, original_supply=None,
                 internal=True, is_coupled=False, minimum_supply=None, primary_energy_factor = None, el_factor = 0,
                 eff_in = 1):
        self.name = name
        self.supply = supply
        self.price = price
        self.connections = connections
        self.co2_equivalent = co2_equivalent
        self.internal = internal
        self.is_coupled = is_coupled
        self.minimum_supply = minimum_supply
        self.primary_energy_factor = primary_energy_factor
        self.electricity_production_factor = el_factor
        self.efficiency_in = eff_in
        self.network = network
        if not original_supply:
            self.original_supply = supply
        else:
            self.original_supply = original_supply

    def __str__(self):
        return f"{self.name} supplies {self.supply} @ {self.price} €/kWh"
