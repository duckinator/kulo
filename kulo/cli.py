#!/usr/bin/env python3

"""\
kulo
    Prints a summary of the status of all units.
    (Shortcut for `kulo status` with no arguments.)

kulo help
    Print this help text.

kulo login
    Generate `kulo.toml`.

kulo status [UNIT]
    If UNIT is specified: prints a summary of the status of UNIT.
    Otherwise: prints a summary of the status of all units.

kulo mode UNIT
    Prints the mode that the specified unit is in.

kulo mode UNIT MODE
    Changes the specified unit's mode.

kulo heat-target UNIT [TEMP]
    Get or set the temperature target (aka set-point) when in heat mode.
    TEMP is the target temperature, in degrees Fahrenheit.

kulo cool-target UNIT [TEMP]
    Get or set the temperature target (aka set-point) when in cool mode.
    TEMP is the target temperature, in degrees Fahrenheit.

kulo target UNIT [TEMP]
    Get or set the temperature target (aka set-point) for the current mode.
    When UNIT is in heating mode, equivalent to `kulo heat-target UNIT [TEMP]`.
    When UNIT is in cooling mode, equivalent to `kulo cool-target UNIT [TEMP]`.
    Otherwise, returns an error.
"""

import sys
from . import api

def _ensure_config_file_exists():
    if not api.Kulo().has_config():
        sys.exit(f"ERROR: Config file {api.CONFIG_FILE} does not exist; see `kulo help` for how to generate it.")


def cmd_login():
    api.Kulo().login()
    print(f"Saved config file: {api.CONFIG_FILE}")


def cmd_help():
    sys.exit(__doc__)


def cmd_status(unit_name=None):
    _ensure_config_file_exists()
    kulo = api.Kulo()
    if unit_name:
        unit = kulo.get_unit(unit_name)
        print(kulo.unit_summary(unit))
    else:
        print(kulo.system_status())


def cmd_mode(unit, mode=None):
    _ensure_config_file_exists()
    kulo = api.Kulo()

    if not mode:
        print(kulo.get_mode(unit))
        return

    (old_mode, new_mode) = kulo.set_mode(unit, mode)
    print(f"{unit}: Mode changed from {old_mode} to {new_mode}")


def cmd_cooling_target(unit, setpoint=None):
    _ensure_config_file_exists()
    kulo = api.Kulo()

    if not setpoint:
        print(kulo.get_cool_setpoint(unit))
        return

    (old_setpoint, new_setpoint, mode) = kulo.set_cool_setpoint(unit, setpoint)
    print(f"{unit}: Target temperature for cooling changed from {old_setpoint} to {new_setpoint}.")


def cmd_heating_target(unit, setpoint=None):
    _ensure_config_file_exists()
    kulo = api.Kulo()

    if not setpoint:
        print(kulo.get_heat_setpoint(unit))
        return

    (old_setpoint, new_setpoint, mode) = kulo.set_setpoint(unit, setpoint)
    print(f"{unit}: Target temperature for heating changed from {old_setpoint} to {new_setpoint}.")


def cmd_target(unit, setpoint=None):
    _ensure_config_file_exists()
    mode = api.Kulo().get_mode()

    if mode == 'cool':
        return cmd_cooling_target(unit, setpoint)
    elif mode == 'heat':
        return cmd_heating_target(unit, setpoint)
    else:
        raise KuloException(f"{unit}: Not currently in 'cool' or 'heat' modes; please use `kulo cooling-target` or `kulo heating-target` commands.")


COMMANDS = {
    'help': cmd_help,
    'login': cmd_login,
    'status': cmd_status,
    'mode': cmd_mode,
    'cool-target': cmd_cooling_target,
    'cooling-target': cmd_cooling_target,
    'heat-target': cmd_heating_target,
    'heating-target': cmd_heating_target,
    'target': cmd_target,
}
DEFAULT_COMMAND = 'status'


def main(argv=sys.argv):
    if any(arg in argv for arg in ['--help', '-h', 'help']):
        cmd_help()

    args = argv.copy()

    _script_path = args.pop(0)
    command = DEFAULT_COMMAND

    if len(argv) > 1:
        command = args.pop(0)

    try:
        COMMANDS[command](*args)
    except api.KuloException as e:
        sys.exit(f"kulo: error: {str(e)}")
