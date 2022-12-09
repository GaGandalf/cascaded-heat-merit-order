from datetime import datetime, timedelta
import pandas as pd
import logging
from typing import List

from meteostat import Point, Hourly

from cascaded_heat_merit_order.location import Location

reference_df = None


def load_reference(filepath_or_buffer):
    global reference_df
    reference_df = pd.read_csv(filepath_or_buffer, sep=";", header=0, index_col=0, parse_dates=True)


def celsius_to_kelvin(t: float):
    return t + 273.15


def find_fuel_price(timestamp: datetime, fuel_price_reference: pd.Series = None):
    """if fuel_price_reference.any():
        try:
            return fuel_price_reference.loc[timestamp]
        except KeyError as ke:
            logging.warning(f"Fuel price not found at {timestamp}. Using mean.")
            return fuel_price_reference.mean()"""
    try:
        if isinstance(globals()["reference"], pd.DataFrame):
            return globals()["reference"]['fuel_price'][timestamp]
    except KeyError:
        logging.debug("No fuel prices in reference found! Using default value.")
        logging.debug(f"Used default price at {timestamp}")
        default_price = 0.08  # €/kWh
        return default_price


def find_electricity_price(timestamp: datetime, electricity_price_reference=None):
    if electricity_price_reference is not None:
        try:
            return electricity_price_reference.loc[timestamp]
        except KeyError as ke:
            logging.warning(f"Electricity price not found at {timestamp}. Using mean from reference.")
            return electricity_price_reference.mean()
    else:
        try:
            if isinstance(globals()["reference"], pd.DataFrame):
                return globals()["reference"]['electricity_price'][timestamp]
        except KeyError:
            logging.debug("No electricity prices in reference found! Using default value.")
            default_price = 0.2  # €/kWh
            logging.debug(f"Used default price at {timestamp}")
            return default_price


def find_ambient_temperature(timestamp: datetime) -> float:
    try:
        if isinstance(globals()["reference"], pd.DataFrame):
            return globals()["reference"]['t_ambient'][timestamp]
    except KeyError:
        logging.debug("Reference does not contain temperature information. Using default.")
        t_ambient = celsius_to_kelvin(20)
        logging.debug(f"Used default temperature at {timestamp}")
        return t_ambient


def find_electricity_co2_equivalence(timestamp: datetime):
    logging.info("CO2 Equivalence for electricity is constant @550g/kWh")
    return 550


def datetime_range(start: datetime, end: datetime, delta: timedelta):
    return [dt for dt in (datetime_range_generator(start, end, delta))]


def datetime_range_generator(start: datetime, end: datetime, delta: timedelta):
    """
    source: https://stackoverflow.com/questions/39298054/generating-15-minute-time-interval-array-in-python

    :param start:
    :param end:
    :param delta:
    :return:
    """
    current = start
    while current < end:
        yield current
        current += delta


def set_up_merit_order_calculation(filepath):
    """
    This function loads reference data into global variables to be accessible for energy-converters and network-
    connectors during the merit-order calculation.
    """

    try:
        reference_data = pd.read_pickle(filepath)
        globals()['reference'] = reference_data

    except FileNotFoundError:
        globals()['reference'] = None
        logging.warning("Reference data not found! Using defaults.")
        logging.debug("Reference data should be placed in root/data/reference.csv")


def get_weather_df_hourly(timeframe: List[datetime],
                          location: Location):
    """
    @param: timeframe - array of 2 datetime objects, start and finish
    @param: location - array of coordinates lat/long (floats) default @ETA-Fabrik TU Darmstadt

    returns: pandas df with hourly weather data for location
    """
    # Get location for meteostat
    location = Point(location.latitude, location.longitude)
    # Get hourly data for datetime period
    data = Hourly(location, timeframe[0], timeframe[1])
    data = data.fetch()
    return (data)
