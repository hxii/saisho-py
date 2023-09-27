import configparser
import os
from pathlib import Path

import click

from ..engine import TerminalPrint, saisho_engine


@click.command("upload")
@click.option(
    "--config", "-c", show_default=True, default="ssh.conf", help="Config file with SSH credentials", type=Path
)
def upload(config: Path):
    if config.exists():
        c = configparser.ConfigParser()
        c.read(config)
        if not validate_config(c):
            TerminalPrint.error("Config file invalid! See 'ssh.conf.sample' for instructions!")
            exit(1)
        command = build_command(c.items("ssh"))
    else:
        TerminalPrint.error(f"Config file {config} doesn't exist. Aborting!")


def build_command(pairs):
    for key, value in pairs:
        print(key, value)


def validate_config(config: configparser.ConfigParser):
    parts = ("user", "pass", "host", "path")
    if "ssh" in config.sections():
        return set(parts).issubset(config.options("ssh"))
    return False
