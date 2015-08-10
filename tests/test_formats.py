# -*- coding: utf-8 -*-
from dmutils.formats import (
    get_label_for_lot_param, lot_to_lot_case,
    format_price, format_service_price
)
import pytest


class TestFormats(object):

    def test_returns_lot_in_lot_case(self):

        cases = [
            ("saas", "SaaS"),
            ("iaas", "IaaS"),
            ("paas", "PaaS"),
            ("scs", "SCS"),
            ("dewdew", None),
        ]

        for example, expected in cases:
            assert lot_to_lot_case(example) == expected

    def test_returns_label_for_lot(self):

        cases = [
            ("saas", "Software as a Service"),
            ("iaas", "Infrastructure as a Service"),
            ("paas", "Platform as a Service"),
            ("scs", "Specialist Cloud Services"),
            ("dewdew", None),
        ]

        for example, expected in cases:
            assert get_label_for_lot_param(example) == expected


def test_format_service_price():
    service = {
        'priceMin': '12.12',
        'priceMax': '13.13',
        'priceUnit': 'Unit',
        'priceInterval': 'Second',
    }

    cases = [
        ('12.12', u'£12.12 to £13.13 per unit per second'),
        ('', ''),
        (None, ''),
    ]

    def check_service_price_formatting(price_min, formatted_price):
        service['priceMin'] = price_min
        assert format_service_price(service) == formatted_price

    for price_min, formatted_price in cases:
        yield check_service_price_formatting, price_min, formatted_price


def test_format_price():
    cases = [
        ((u'12', None, 'Unit', None), u'£12 per unit'),
        (('12', '13', 'Unit', None), u'£12 to £13 per unit'),
        (('12', '13', 'Unit', 'Second'), u'£12 to £13 per unit per second'),
        (('12', None, 'Unit', 'Second'), u'£12 per unit per second'),
    ]

    def check_price_formatting(args, formatted_price):
        assert format_price(*args) == formatted_price

    for args, formatted_price in cases:
        yield check_price_formatting, args, formatted_price


def test_format_price_errors():
    cases = [
        ('12', None, None, None),
        (None, None, None, None),
    ]

    def check_price_formatting(case):
        with pytest.raises((TypeError, AttributeError)):
            format_price(*case)

    for case in cases:
        yield check_price_formatting, case