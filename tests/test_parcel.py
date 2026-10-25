import unittest
from parcel import shipping_cost


class ShippingTests(unittest.TestCase):
    def test_small_parcel(self):
        self.assertEqual(shipping_cost(1000, 500), 500)

    def test_first_kilogram_boundary(self):
        self.assertEqual(shipping_cost(1000, 1000), 500)

    def test_second_kilogram(self):
        self.assertEqual(shipping_cost(1000, 1001), 600)

    def test_free_shipping_threshold(self):
        self.assertEqual(shipping_cost(5000, 1000), 0)

    def test_above_free_shipping_threshold(self):
        self.assertEqual(shipping_cost(5001, 1000), 0)

    def test_express_surcharge(self):
        self.assertEqual(shipping_cost(1000, 500, express=True), 1750)

    def test_free_standard_does_not_remove_express_charge(self):
        self.assertEqual(shipping_cost(5000, 500, express=True), 1250)

    def test_maximum_weight(self):
        self.assertEqual(shipping_cost(1000, 20000), 2400)

    def test_negative_subtotal(self):
        with self.assertRaises(ValueError):
            shipping_cost(-1, 500)

    def test_fractional_subtotal(self):
        with self.assertRaises(ValueError):
            shipping_cost(10.5, 500)

    def test_invalid_weights(self):
        for weight in (0, -1, 20001, 1.5, True):
            with self.subTest(weight=weight), self.assertRaises(ValueError):
                shipping_cost(1000, weight)

    def test_invalid_express(self):
        with self.assertRaises(ValueError):
            shipping_cost(1000, 500, express="yes")
