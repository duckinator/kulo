"""High-level Python API for interacting with Kumo cloud."""

import binascii
from pathlib import Path
import pykumo
#from pykumo.py_kumo_base import _LOGGER as pykb_LOGGER
from pykumo.py_kumo import PyKumo
import toml


class KuloException(Exception):
    """Exceptions raised by an kulo.api.Kulo instance."""
    pass


class Kulo:
    """
    API client for interacting with Kumo Cloud mostly-locally.

    ```
    from kulo.api import Kulo
    kulo = Kulo(config_file)
    if not kulo.has_config():
        kulo.login()

    print(kulo.summary_all_units())
    ```

    Known modes are:
    - off
    - auto
    - dry
    - heat
    - cool
    - vent
    """

    def __init__(self, config_file):
        self.config_file = Path(config_file)
        if self.has_config():
            self.config = self.load_config()
        else:
            self.config = None

    def has_config(self):
        if self.config_file.exists():
            return True
        return False

    def load_config(self):
        config = toml.loads(self.config_file.read_text(encoding="utf-8"))

        return {
            name: PyKumo(unit_config['name'],
                         unit_config['ip'],
                        self._b64_encode_credentials(unit_config['credentials']),
                        None,
                        None) for name, unit_config in config.items()}

    @staticmethod
    def _c_to_f(temp_c):
        return temp_c * 9 / 5 + 32


    def format_temp(self, temp_c):
        temp_f = self._c_to_f(temp_c)
        return f"{temp_f}\u00BAF"


    @staticmethod
    def _b64_encode_credentials(creds):
        """Formats given credentials in a way that works for local communication."""
        return {
            'crypto_serial': bytearray(creds['crypto_serial']).hex(),
            'password': binascii.b2a_base64(bytes(creds['password']), newline=False).decode('utf-8'),
        }

    @staticmethod
    def _get_units_for_account(account):
        units = account.make_pykumos()
        for name in units:
            units[name].update_status()
        return units


    @staticmethod
    def unit_config(unit):
        return {
            'name': unit['_name'],
            'ip': unit['_address'],
            'credentials': unit['_security']
        }


    def login(self):
        account = pykumo.KumoCloudAccount.Factory()
        account.get_indoor_units()

        pykumo_units = account.make_pykumos()
        units = {}
        for name in pykumo_units:
            unit = pykumo_units[name]
            unit.update_status()
            units[name] = {
                'name': unit.get_name(),
                'ip': unit.__dict__['_address'],
                'credentials': unit.__dict__['_security'],
            }

        self.config_file.write_text(toml.dumps(units), encoding="utf-8")
        self.load_config()


    def _unit_from_unit_config(self, ucfg):
        return PyKumo(ucfg['name'], ucfg['ip'], self._b64_encode_credentials(ucfg['credentials']), None, None)


    def units_from_config(self, cfg):
        return map(self._unit_from_unit_config, cfg.values())


    def unit_summary(self, unit):
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

        # the +1 is to account for zero-indexing.
        fan_speed_number = valid_fan_speeds.index(current_fan_speed) + 1
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
            f"Temperature:  {self.format_temp(unit.get_current_temperature())}",
            f"Mode:         {mode}",
            f"Fan speed:    {current_fan_speed} ({fan_speed_number}/{num_fan_speeds})",
        ]

        set_point = None
        if mode == 'cool':
            set_point = unit.get_cool_setpoint()
            lines += [
                f"Target:       <={self.format_temp(set_point)}",
            ]

        if mode == 'heat':
            set_point = unit.get_heat_setpoint()
            lines += [
                f"Target:       >={self.format_temp(set_point)}",
            ]

        lines += [
            "",
            f"Valid modes:      {', '.join(mode for mode in modes if mode)}",
            f"Valid fan speeds: {', '.join(valid_fan_speeds)}",
        ]

        return '\n    '.join(lines)


    def summary_all_units(self):
        return "\n\n".join(self.unit_summary(unit) for unit in self.config.values())


    def system_status(self):
        return self.summary_all_units()


    def get_unit(self, unit_name):
        if unit_name not in self.config:
            raise KuloException(f"No such unit {unit_name}; valid options are {', '.join(self.config.keys())}")

        unit = self.config[unit_name]
        unit.update_status()
        return unit


    def get_unit_modes(self, unit):
        if unit is str:
            unit = self.get_unit(unit)

        modes = {
            'off': True,
            'auto': unit.has_auto_mode(),
            'dry': unit.has_dry_mode(),
            'heat': unit.has_heat_mode(),
            'cool': True,
            'vent': unit.has_vent_mode(),
        }
        return [mode for mode in modes if mode]


    def get_mode(self, unit_name):
        return self.get_unit(unit_name).get_mode()


    def set_mode(self, unit_name, mode):
        """
        Set the mode for the designated unit.

        If this function returns, it successfully updated the mode.

        Returns a tuple of +(old_mode, new_mode)+.
        """
        unit = self.get_unit(unit_name)

        valid_modes = self.get_unit_modes(unit)
        if mode not in valid_modes:
            raise KuloException(f"Unsupported mode {repr(mode)} for {repr(unit_name)}.\n\nValid modes are: {', '.join(valid_modes)}")

        old_mode = unit.get_mode()

        unit.set_mode(mode)

        unit.update_status()
        new_mode = unit.get_mode()

        if new_mode != mode:
            raise KuloException(f"Failed to set mode to {mode}. (It's still {new_mode}.)")

        return (old_mode, new_mode)


    def get_setpoint(self, name):
        raise NotImplementedError

    def set_setpoint(self, name, setpoint):
        raise NotImplementedError
