"""High-level Python API for interacting with Kumo cloud."""

import binascii
import pykumo
#from pykumo.py_kumo_base import _LOGGER as pykb_LOGGER
from pykumo.py_kumo import PyKumo
import toml


MODE_LABELS = {
    'off': 'off',
    'auto': 'auto',
    'dry': 'dry',
    'heat': 'heat',
    'cool': 'cool',
    'vent': 'fan',
}


def _c_to_f(temp_c):
    return temp_c * 9 / 5 + 32


def format_temp(temp_c):
    temp_f = _c_to_f(temp_c)
    return f"{temp_f}\u00BAF"


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


def login():
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

    modes = {
        'off': True,
        'auto': unit.has_auto_mode(),
        'dry': unit.has_dry_mode(),
        'heat': unit.has_heat_mode(),
        'cool': True,
        'vent': unit.has_vent_mode(),
    }

    valid_fan_speeds = unit.get_fan_speeds()
    current_fan_speed = unit.get_fan_speed()

    fan_speed_number = valid_fan_speeds.index(current_fan_speed)
    # the -1 is to account for `auto`, which isn't really a speed.
    num_fan_speeds = len(valid_fan_speeds) - 1

    lines = [
        unit.get_name(),
    ]

    if unit.get_defrost():
        lines += ["UNIT IS DEFROSTING"]

    if unit.get_standby():
        lines += ["UNIT IS IN STANDBY"]

    if unit.get_filter_dirty():
        lines += ["Filter needs to be cleaned."]


    humidity = unit.get_current_humidity()
    if humidity:
        lines += [
            f"Humidity:     {humidity}%"
        ]

    mode = unit.get_mode()
    lines += [
        f"Temperature:  {format_temp(unit.get_current_temperature())}",
        f"Mode:         {MODE_LABELS[mode]}",
        f"Fan speed:    {current_fan_speed} ({fan_speed_number}/{num_fan_speeds})",
    ]

    set_point = None
    if mode == 'cool':
        set_point = unit.get_cool_setpoint()
        lines += [
            f"Target:       <={format_temp(set_point)}",
        ]

    if mode == 'heat':
        set_point = unit.get_heat_setpoint()
        lines += [
            f"Target:       >={format_temp(set_point)}",
        ]

    lines += [
        "",
        f"Valid modes:      {', '.join(mode for mode in modes if mode)}",
        f"Valid fan speeds: {', '.join(valid_fan_speeds)}",
    ]

    return '\n    '.join(lines)


def summary_all_units(cfg):
    return "\n\n".join(unit_summary(unit) for unit in units_from_config(cfg))


def system_status(path):
    return summary_all_units(load_config(path))
