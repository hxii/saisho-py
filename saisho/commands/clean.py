import click

from ..engine import TerminalPrint, saisho_engine


@click.command("clean")
def clean():
    count = 0
    for file in saisho_engine.OUTPUT_FOLDER.iterdir():
        file.unlink()
        count += 1
    TerminalPrint.success(f"Removed {count} file(s)")
