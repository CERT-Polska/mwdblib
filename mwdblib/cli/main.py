import functools

import click
from click.globals import get_current_context

from .. import __version__
from ..core import MWDB
from ..exc import MWDBError, NotAuthenticatedError


def pass_mwdb(fn):
    @click.option("--api-url", type=str, default=None, help="URL to MWDB instance API")
    @click.option(
        "--config-path", type=str, default=None, help="Alternative configuration path"
    )
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        ctx = get_current_context()
        mwdb_options = {}
        api_url = kwargs.pop("api_url")
        if api_url:
            mwdb_options["api_url"] = api_url
        config_path = kwargs.pop("config_path")
        if config_path:
            mwdb_options["config_path"] = config_path
        mwdb = MWDB(**mwdb_options)
        try:
            return fn(mwdb=mwdb, *args, **kwargs)
        except NotAuthenticatedError:
            click.echo(
                "Error: Not authenticated. Use `mwdb login` first to set credentials.",
                err=True,
            )
            ctx.abort()
        except MWDBError as error:
            click.echo(
                "{}: {}".format(error.__class__.__name__, error.args[0]), err=True
            )
            ctx.abort()

    return wrapper


@click.group()
def main():
    """MWDB Core API client"""
    pass


@main.command("version")
def version():
    """Prints mwdblib version"""
    click.echo(__version__)


@main.command("server")
@pass_mwdb
def server(mwdb):
    """Prints current server URL and version"""
    click.echo(f"{mwdb.options.api_url} ({mwdb.api.server_version})")
