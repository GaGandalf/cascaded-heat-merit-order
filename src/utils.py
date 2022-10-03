from datetime import datetime, timedelta

import pandas as pd
import logging


def celsius_to_kelvin(t: float | int):
    return t + 273.15


def find_fuel_price(timestamp: datetime, fuel_price_reference: pd.Series = None):
    if fuel_price_reference.any():
        try:
            return fuel_price_reference.loc[timestamp]
        except KeyError as ke:
            logging.warning(f"Fuel price not found at {timestamp}. Using mean.")
            return fuel_price_reference.mean()
    default_price = 0.08
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
            reference = globals()['reference']
            return reference['electricity_price'][timestamp]

        except KeyError:
            default_price = 0.2
            return default_price


def find_ambient_temperature(timestamp: datetime):
    try:
        reference = globals()['reference']
        return reference['t_ambient'][timestamp]

    except KeyError:
        default_price = 0.2
        return default_price


def find_electricity_co2_equivalence(timestamp: datetime):
    # ToDo: Implementation of CO2 Equivalence of electricity in relationship to the electricity supply mix on site
    return 0.478


def datetime_range(start: datetime, end: datetime, delta: timedelta):
    return [dt for dt in (datetime_range_gen(start, end, delta))]


def datetime_range_gen(start: datetime, end: datetime, delta: timedelta):
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


def set_up_merit_order_calculation():
    """
    This function loads reference data into global variables to be accessible for energy-converters and network-
    connectors during the merit-order calculation.
    """
    try:
        reference_data = pd.read_csv("data/reference.csv")
        globals()['reference'] = reference_data

    except FileNotFoundError:
        logging.warning("Reference data not found! Using defaults.")
        logging.debug("Reference data should be placed in root/data/reference.csv")
