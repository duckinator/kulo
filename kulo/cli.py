#!/usr/bin/env python3

"""
kulo help
    Print this help text.

kulo login
    Generate `kulo.toml`.

kulo status
kulo
    Interactive control of the devices specified in `kulo.toml`.
"""

import sys
from . import api

CONFIG_FILE = 'kulo.toml'

def _ensure_config_file_exists():
    if not api.Kulo(CONFIG_FILE).has_config():
        sys.exit(f"ERROR: Config file {CONFIG_FILE} does not exist; see `kulo help` for how to generate it.")


def cmd_login():
    api.Kulo(CONFIG_FILE).login()
    print(f"Saved config file: {CONFIG_FILE}")


def cmd_help():
    sys.exit(__doc__)


def cmd_status():
    _ensure_config_file_exists()
    print(api.Kulo(CONFIG_FILE).system_status())


def cmd_mode(unit, mode=None):
    _ensure_config_file_exists()
    kulo = api.Kulo(CONFIG_FILE)

    if not mode:
        print(kulo.get_mode(unit))

    (old_mode, new_mode) = kulo.set_mode(unit, mode)
    print(f"{unit}: Mode changed from {old_mode} to {new_mode}")

COMMANDS = {
    'help': cmd_help,
    'login': cmd_login,
    'status': cmd_status,
    'mode': cmd_mode,
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
