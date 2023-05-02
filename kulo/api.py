"""High-level Python API for interacting with Kumo cloud."""

import binascii
import pykumo
#from pykumo.py_kumo_base import _LOGGER as pykb_LOGGER
from pykumo.py_kumo import PyKumo
import toml


def _b64_encode_credentials(creds):
    """Formats given credentials in a way that works for local communication."""
    return {
        'crypto_serial': bytearray(creds['crypto_serial']).hex(),
        'password': binascii.b2a_base64(bytes(creds['password']), newline=False).decode('utf-8'),
    }

def _get_units_for_account(account):
    units = account.make_pykumos()
    for name in units:
        units[name].update_status()
    return units


def unit_config(unit):
    return {
        'name': unit['_name'],
        'ip': unit['_address'],
        'credentials': unit['_security']
    }


def generate_config():
    account = pykumo.KumoCloudAccount.Factory()
    account.get_indoor_units()

    units = _get_units_for_account(account)

    return {name: unit_config(units[name].__dict__) for name in units}


def load_config(path):
    config = toml.load(path)

    for name, unit_cfg in config.items():
        assert 'name' in unit_cfg
        assert 'ip' in unit_cfg
        assert 'credentials' in unit_cfg

        assert 'crypto_serial' in unit_cfg['credentials']
        assert 'password' in unit_cfg['credentials']

    return config


def unit_from_unit_config(ucfg):
    return PyKumo(ucfg['name'], ucfg['ip'], _b64_encode_credentials(ucfg['credentials']), None, None)


def units_from_config(cfg):
    return map(unit_from_unit_config, cfg.values())


def unit_summary(unit):
    unit.update_status()
    udict = unit.__dict__

    profile = udict['_profile']
    status = udict['_status']
    has_mode = {
        'auto': profile['hasModeAuto'],
        'dry': profile['hasModeDry'],
        'heat': profile['hasModeHeat'],
        'cool': True,
        'fan': profile['hasModeVent']
    }
    num_fan_speeds = profile['numberOfFanSpeeds']

    lines = [
        udict['_name'],
    ]

    if status['defrost']:
        lines += ["UNIT IS DEFROSTING"]

    if status['standby']:
        lines += ["UNIT IS IN STANDBY"]


    humidity = udict.get('_mhk2', {}).get('indoorHumidity', None)
    if humidity:
        lines += [
            f"Humidity:     {humidity}"
        ]

    lines += [
        f"Temperature:  {status['roomTemp']}C (TODO: convert to F)",
        f"Mode:         {status['mode']}",
        f"Fan speed:    {status['fanSpeed']}",
    ]

    return '\n    '.join(lines)


def summary_all_units(cfg):
    return "\n\n".join(unit_summary(unit) for unit in units_from_config(cfg))


def system_status(path):
    return summary_all_units(load_config(path))
