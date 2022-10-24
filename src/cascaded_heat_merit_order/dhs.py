from datetime import datetime

from cascaded_heat_merit_order.location import Location
from cascaded_heat_merit_order.utils import celsius_to_kelvin, get_weather_df_hourly
import pandas as pd
from sklearn.preprocessing import StandardScaler


class DHS:
    def __init__(self, name: str, location: Location, min_temp: float = celsius_to_kelvin(60),
                 max_temp: float = celsius_to_kelvin(120), demand_profile: pd.Series = None,
                 heat_sources=None, heat_demands=None, use_demand_profile=True, demand_regression_model=None
                 ):
        self.name = name
        self.location = location
        self.minimum_feed_in_temperature = min_temp
        self.maximum_feed_in_temperature = max_temp
        self.demand_profile = demand_profile

        self.heat_sources = heat_sources
        self.heat_demands = heat_demands
        self.use_demand_profile = use_demand_profile
        self.demand_regression_model = demand_regression_model

    def estimate_demand_profile(self, timeframe=[datetime(2021, 1, 1), datetime(2022, 1, 1)], inplace=False,
                                scaling_factor=1):
        df_weather = get_weather_df_hourly(self.location, timeframe)
        x = df_weather.to_numpy()
        scaler = StandardScaler()
        x = scaler.fit_transform(x)
        predicted_dhs_load = self.demand_regression_model.predict(x)
        df_weather["predicted_load"] = predicted_dhs_load * scaling_factor
        if inplace:
            self.demand_profile = df_weather["predicted_load"]
        return df_weather["predicted_load"]