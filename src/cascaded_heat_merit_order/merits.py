class Merit:
    def __init__(self, name_source: str, name_sink: str, supply: float, price: float, co2_intensity=0, original_supply=None,
                 connections=None, sink_internal=True, source_internal=True
                 ) -> object:
        self.name_source = name_source
        self.name_sink = name_sink
        self.supply = supply
        self.price = price
        self.connections = connections
        self.co2_intensity = co2_intensity
        self.sink_internal = sink_internal
        self.source_internal = source_internal
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
    def __init__(self, name: str, demand: float, price: float):
        self.name = name
        self.demand = demand
        self.price = price


    def __str__(self):
        return f"{self.name} demands {self.demand} @ {self.price} €/kWh"


class SupplyMerit:
    def __init__(self, name: str, supply: float, price: float, co2_equivalent=0, connections=None, original_supply=None,
                 internal=True):
        self.name = name
        self.supply = supply
        self.price = price
        self.connections = connections
        self.co2_equivalent = co2_equivalent
        self.internal = internal
        if not original_supply:
            self.original_supply = supply
        else:
            self.original_supply = original_supply

    def __str__(self):
        return f"{self.name} supplies {self.supply} @ {self.price} €/kWh"
