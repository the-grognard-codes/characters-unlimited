"""Whole-catalog ordinary formula acquisition and exact retained replay."""

from copy import deepcopy
from .recorded_formulas import MAX_INTEGER, validate_formula, formula_value, roll_formula


def validate_acquisition_catalog(catalog):
    if not isinstance(catalog, dict) or len(catalog) > 1000:
        raise ValueError('Acquisitions require a bounded formula catalog')
    for identifier, groups in catalog.items():
        if (not isinstance(identifier, str) or not identifier.strip() or not isinstance(groups, dict) or
                len(groups) > 1000 or any(not isinstance(key, str) or not key.strip() for key in groups)):
            raise ValueError('Acquisition formula groups need nonempty identities')
        for formula in groups.values():
            validate_formula(formula)
            bounds = ((formula['count'] + formula.get('constant', 0)) * formula.get('multiplier', 1),
                      (formula['count'] * formula['sides'] + formula.get('constant', 0)) * formula.get('multiplier', 1))
            if any(abs(value) > MAX_INTEGER for value in bounds):
                raise ValueError('Acquisition formula can exceed the exact integer range')


def validate_cached_acquisitions(catalog, acquisitions, *, record_constants=True):
    validate_acquisition_catalog(catalog)
    if type(record_constants) is not bool:
        raise ValueError('Constant receipt policy must be boolean')
    if not isinstance(acquisitions, dict) or set(acquisitions) - set(catalog):
        raise ValueError('Acquisitions must use known catalog identities')
    for identifier, receipt in acquisitions.items():
        groups = {key: formula for key, formula in catalog[identifier].items() if record_constants or formula['count']}
        if (not isinstance(receipt, dict) or set(receipt) != {'rolls'} or not isinstance(receipt['rolls'], dict) or
                set(receipt['rolls']) != set(groups)):
            raise ValueError('Acquisition receipts must match their pinned formula groups')
        for key, formula in groups.items():
            formula_value(formula, receipt['rolls'][key])


def acquire_selected(catalog, acquisitions, selections, die, *, record_constants=True):
    """Validate everything first; return a copy retaining inactive and reselected dice."""
    validate_cached_acquisitions(catalog, acquisitions, record_constants=record_constants)
    if (not isinstance(selections, list) or len(selections) > 1000 or
            any(not isinstance(item, str) or item not in catalog for item in selections) or
            len(set(selections)) != len(selections)):
        raise ValueError('Acquisition selections must be distinct known identities')
    result = deepcopy(acquisitions)
    for identifier in selections:
        if identifier not in result:
            result[identifier] = {'rolls': {key: roll_formula(formula, die)
                for key, formula in catalog[identifier].items() if record_constants or formula['count']}}
    return result
