import click
import functools

from click.globals import get_current_context

from ..core import MWDB
from ..exc import MWDBError
from .. import __version__


def pass_mwdb(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        ctx = get_current_context()
        mwdb = MWDB(**ctx.obj.get("mwdb_options", {}))
        try:
            return fn(mwdb=mwdb, *args, **kwargs)
        except MWDBError as error:
            click.echo("{}: {}".format(error.__class__.__name__, error.args[0]), err=True)
            ctx.abort()
    return wrapper


@click.group()
@click.option("--api-url", type=str, default=None,
              help="URL to MWDB instance API")
@click.option("--config-path", type=str, default=None,
              help="Alternative configuration path")
@click.pass_context
def main(ctx, api_url, config_path):
    ctx.ensure_object(dict)
    mwdb_options = ctx.obj["mwdb_options"] = {}
    if api_url is not None:
        mwdb_options["api_url"] = api_url
    if config_path is not None:
        mwdb_options["config_path"] = config_path


@main.command("version")
def version():
    """Prints mwdblib version"""
    click.echo(__version__)
