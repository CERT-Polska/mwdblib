import click
from .. import __version__


@click.group()
@click.option("--api-url", type=str, default=None,
              help="URL to Malwarecage instance API")
@click.pass_context
def main(ctx, api_url):
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url


@main.command("version")
def version():
    """Prints mwdblib version"""
    click.echo(__version__)
