from cascaded_heat_merit_order.energy_converters import EnergyConverter
from cascaded_heat_merit_order.networks import HeatNetwork


class NetworkConnector(EnergyConverter):
    """
    This data type connects heat-networks. Connectors can bei either heat-pumps or heat-exchangers
    For parametrizing the COP we use the "Gütegrad (Grade)" of the heat pump and calculate the inverse Carnot
    efficiency from the network input and output temperatures.

    Network connectors are unaware of their role. Their role is determined by comparing the heat-sink temperature
    and the heat-source temperature.

    A heat exchanger transfers heat from a high temperature network to a low temperature network.
    A heatpump uses electricity to drive an amount of heat Q from a lower temperature reservoir to a
    higher temperature reservoir
    """

    def __init__(self, name: str,
                 heat_sink: HeatNetwork, heat_source: HeatNetwork,
                 max_throughput: float = None,
                 price: float = 0,
                 efficiency: float = 1):
        EnergyConverter.__init__(self, name, internal=True)
        self.heat_sink = heat_sink
        self.heat_source = heat_source
        self.max_throughput = max_throughput
        self.price = price
        self.efficiency = efficiency


class HeatPump(NetworkConnector):
    def __init__(self, name: str,
                 heat_sink: HeatNetwork, heat_source: HeatNetwork,
                 max_throughput: float = None,
                 efficiency=1,
                 price: float = 0):
        NetworkConnector.__init__(self, name, heat_sink=heat_sink, heat_source=heat_source,
                                  max_throughput=max_throughput, price=price, efficiency=efficiency)

    def get_cop(self, efficiency):
        cop_theoretical = self.heat_sink.operating_temperature / (self.heat_sink.operating_temperature
                                                                  - self.heat_source.operating_temperature)
        cop = cop_theoretical * efficiency
        cop = round(cop, 5)
        return cop


class HeatExchanger(NetworkConnector):
    def __init__(self, name: str,
                 heat_sink: HeatNetwork, heat_source: HeatNetwork,
                 efficiency: float = 1,
                 max_throughput: float = None,
                 price: float = 0):
        NetworkConnector.__init__(self, name, heat_sink=heat_sink, heat_source=heat_source,
                                  max_throughput=max_throughput, price=price, efficiency=efficiency)
