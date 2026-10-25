"""A tiny parcel checkout, priced in integer cents."""
import os


def shipping_cost(subtotal, weight_grams, express=False):
    if type(subtotal) is not int or subtotal < 0:
        raise ValueError("subtotal must be a non-negative integer in cents")
    if type(weight_grams) is not int or not 0 < weight_grams <= 20000:
        raise ValueError("weight must be between 1 and 20000 grams")
    if type(express) is not bool:
        raise ValueError("express must be a boolean")
    # Only the explicitly selected negative demonstration enables this defect.
    free_threshold = 5001 if os.environ.get("PARCEL_DEMO_BUG") == "1" else 5000
    standard = 0 if subtotal >= free_threshold else 500 + ((weight_grams - 1) // 1000) * 100
    return standard + (1250 if express else 0)
