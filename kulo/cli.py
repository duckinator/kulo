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

from pathlib import Path
import sys
import toml
from . import api

CONFIG_FILE = 'kulo.toml'

def _has_config():
    return Path(CONFIG_FILE).exists()


def cmd_login():
    Path(CONFIG_FILE).write_text(toml.dumps(api.login()), encoding="utf-8")
    print(f"Saved config file: {CONFIG_FILE}")

def cmd_help():
    sys.exit(__doc__)

def cmd_status():
    if not _has_config():
        sys.exit(f"ERROR: Config file {CONFIG_FILE} does not exist; see `kulo help` for how to generate it.")

    print(api.system_status(CONFIG_FILE))


COMMANDS = {
    'help': cmd_help,
    'login': cmd_login,
    'status': cmd_status,
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

    COMMANDS[command](*args)
