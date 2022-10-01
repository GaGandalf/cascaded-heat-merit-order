from location import Location
from utils import celsius_to_kelvin
import pandas as pd


class DHS:
    def __init__(self, name: str, location: Location, min_temp: float = celsius_to_kelvin(60),
                 max_temp: float = celsius_to_kelvin(120), demand_profile: pd.Series = None,
                 heat_sources=None, heat_demands=None, use_demand_profile=True
                 ):
        self.name = name
        self.location = location
        self.minimum_feed_in_temperature = min_temp
        self.maximum_feed_in_temperature = max_temp
        self.demand_profile = demand_profile

        self.heat_sources = heat_sources
        self.heat_demands = heat_demands
        self.use_demand_profile = use_demand_profile
