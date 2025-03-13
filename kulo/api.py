"""High-level Python API for interacting with Kumo cloud."""

import binascii
from pathlib import Path
import pykumo
#from pykumo.py_kumo_base import _LOGGER as pykb_LOGGER
from pykumo.py_kumo import PyKumo
import toml

CONFIG_FILE_NAME = 'kulo.toml'

CONFIG_PATH = Path.home() / '.config' / 'kulo'

CONFIG_FILE = CONFIG_PATH / CONFIG_FILE_NAME


class KuloException(Exception):
    """Exceptions raised by a kulo.api.Kulo instance."""
    pass


class Kulo:
    """
    API client for interacting with Kumo Cloud mostly-locally.

    ```
    from kulo.api import Kulo
    kulo = Kulo()
    if not kulo.has_config():
        kulo.login()

    print(kulo.system_status())
    ```

    Known modes are:
    - off
    - auto
    - dry
    - heat
    - cool
    - vent
    """

    def __init__(self):
        self.config_file = Path(CONFIG_FILE)
        if self.has_config():
            self.config = self.load_config()
        else:
            self.config = None

    def has_config(self):
        """Returns True if the config file exists; otherwise, returns False."""
        return self.config_file.exists()

    def load_config(self):
        """
        Load the TOML config file.

        Returns a dict mapping unit names to +PyKumo+ instances.
        """
        config = toml.loads(self.config_file.read_text(encoding="utf-8"))

        return {
            name: PyKumo(unit_config['name'],
                         unit_config['ip'],
                        self._b64_encode_credentials(unit_config['credentials']),
                        None,
                        None) for name, unit_config in config.items()}

    @staticmethod
    def _c_to_f(temp_c):
        """Convert a temperature from Celsius to Fahrenheit."""
        return temp_c * 9 / 5 + 32


    @staticmethod
    def _f_to_c(temp_f):
        """Convert a temperature from Celsius to Fahrenheit."""
        return temp_f - 32 * 5 / 9


    def format_temp(self, temp_c):
        """Pretty-print +temp_c+ (temperature in Celsius), in Fahrenheit."""
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
        """Given a +unit+, return a simplified dict representing the configuration for it."""
        return {
            'name': unit['_name'],
            'ip': unit['_address'],
            'credentials': unit['_security']
        }


    def login(self):
        """
        Log in to Kumo Cloud, fetch the information required to control
        devices locally, and save that information to the file.

        User account information is NEVER saved.
        """

        account = pykumo.KumoCloudAccount.Factory()
        account.get_indoor_units()

        pykumo_units = account.make_pykumos()
        units = {}
        for name, unit in pykumo_units.items():
            unit.update_status()
            units[name] = {
                'name': unit.get_name(),
                'ip': unit.__dict__['_address'],
                'credentials': unit.__dict__['_security'],
            }

        # Create directory the config file goes in.
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Save the config file.
        self.config_file.write_text(toml.dumps(units), encoding="utf-8")

        # Load the config so we can use it immediately.
        self.load_config()


#    def _unit_from_unit_config(self, ucfg):
#        return PyKumo(ucfg['name'], ucfg['ip'], self._b64_encode_credentials(ucfg['credentials']), None, None)


#    def units_from_config(self, cfg):
#        return map(self._unit_from_unit_config, cfg.values())


    def unit_summary(self, unit):
        """
        Returns a summary for the specified +unit+.
        """
        if isinstance(unit, str):
            unit = self.get_unit(unit)

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
        ]

        fan_speed = f"Fan speed:    {current_fan_speed}"
        if current_fan_speed != 'auto':
            fan_speed += f" ({fan_speed_number}/{num_fan_speeds})"
        lines += [fan_speed]

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


    def system_status(self):
        """
        Returns a summary of the state of all units.
        """
        return "\n\n".join(self.unit_summary(unit) for unit in self.config.values())


    def get_unit(self, unit_name):
        """
        Given a +unit_name+, returns the actual unit.
        """
        if unit_name not in self.config:
            raise KuloException(f"No such unit {unit_name}; valid options are {', '.join(self.config.keys())}")

        unit = self.config[unit_name]
        unit.update_status()
        return unit


    def get_unit_modes(self, unit):
        """
        Returns a list of modes that +unit+ supports.

        +unit+ can either be a string (the name of the unit) or an actual
        unit (as is provided in +self.config+).
        """
        if isinstance(unit, str):
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
        """
        Returns the mode +unit_name+ is currently configured for.
        """
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
            raise KuloException(
                f"Unsupported mode {repr(mode)} for {repr(unit_name)}.\n\nValid modes are: {', '.join(valid_modes)}"
            )

        old_mode = unit.get_mode()

        unit.set_mode(mode)

        unit.update_status()
        new_mode = unit.get_mode()

        if new_mode != mode:
            raise KuloException(f"Failed to set mode to {mode}. (It's still {new_mode}.)")

        return (old_mode, new_mode)


    def get_cool_setpoint(self, unit_name):
        """
        Returns +unit_name+'s set-point/target for heating.
        """
        return self.format_temp(self.get_unit(unit_name).get_cool_setpoint())


    def set_cool_setpoint(self, unit_name, setpoint_f):
        """
        set the set-point/target for cooling.

        if this function returns, it successfully updated the set-point.

        returns a tuple of +(old_setpoint, new_setpoint)+.
        """
        unit = self.get_unit(unit_name)

        setpoint_c = self._f_to_c(int(setpoint_f))

        old_setpoint = unit.get_cool_setpoint()

        unit.set_cool_setpoint(setpoint_c)

        unit.update_status()
        new_setpoint = unit.get_cool_setpoint()

        if setpoint_c != new_setpoint:
            raise KuloException(
                f"failed to change cooling setpoint from {old_setpoint}C to {setpoint_c}C.\n"
                f"It's currently set to {new_setpoint}C."
            )

        return (self.format_temp(old_setpoint), self.format_temp(new_setpoint))


    def get_heat_setpoint(self, unit_name):
        """
        Returns +unit_name+'s set-point/target for heating.
        """
        return self.format_temp(self.get_unit(unit_name).get_heat_setpoint())


    def set_heat_setpoint(self, unit_name, setpoint_f):
        """
        set the set-point/target for heating.

        if this function returns, it successfully updated the set-point.

        returns a tuple of +(old_setpoint, new_setpoint)+.
        """
        unit = self.get_unit(unit_name)

        setpoint_c = self._f_to_c(int(setpoint_f))

        old_setpoint = unit.get_heat_setpoint()

        unit.set_heat_setpoint(setpoint_c)

        unit.update_status()
        new_setpoint = unit.get_heat_setpoint()

        if new_setpoint != old_setpoint:
            raise KuloException(f"failed to change heating setpoint to {old_setpoint}C. (It's still {new_setpoint}C.)")

        return (self.format_temp(old_setpoint), self.format_temp(new_setpoint))
