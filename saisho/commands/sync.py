import click


@click.command("sync")
@click.option("--file", "-f", default=None)
def sync(file: str | None):
    """
    (Re)build a file.

    Arguments:
        file -- Optional. If provided, will only build the given file.
    """
    pass
