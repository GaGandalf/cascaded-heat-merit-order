from typing import List

from cascaded_heat_merit_order.merits import Merit


def sum_merit_order_cost(merit_order: List[Merit], internal=True) -> float:
    cost = 0
    for merit in merit_order:
        if merit.sink_internal == internal:
            merit_cost = merit.supply * merit.price
            cost = cost + merit_cost
    return cost

def sum_profit_dhs_sales(merit_order: List[Merit], dhs_price:float,
                         sell_until_demand_met = False) -> float:
    """
    We can either calculate our profits in a way were we have to fulfill acertain dhs demand
    (besicherte lieferung) for this we set sell_until_demadn_met to True. Otherwise we stop selling
    to the dhs once we can no longer make profits by selling. 
    
    """
    profit = 0
    for merit in merit_order:
        if not merit.sink_internal and merit.source_internal:
            if sell_until_demand_met or dhs_price > merit.price:
                merit_profit = merit.supply * (dhs_price - merit.price)
                profit = profit + merit_profit
    return profit


def sum_energy_to_dhs(merit_order: List[Merit]) -> float:
    energy = 0
    for merit in merit_order:
        if not merit.sink_internal:
            energy = energy + merit.supply
    return energy