import click

from ..exc import InvalidCredentialsError, NotAuthenticatedError
from .main import main, pass_mwdb


@main.command("login")
@click.option(
    "--username", "-u", type=str, default=None, help="MWDB user name (default: ask)"
)
@click.option(
    "--password", "-p", type=str, default=None, help="MWDB password (default: ask)"
)
@click.option("--via-api-key", "-A", is_flag=True, help="Use API key provided by stdin")
@click.option(
    "--api-key",
    "-a",
    type=str,
    default=None,
    help="API key token (default: password-based authentication)",
)
@pass_mwdb
@click.pass_context
def login_command(ctx, mwdb, username, password, via_api_key, api_key):
    """Store credentials for MWDB authentication"""
    if via_api_key:
        api_key = click.prompt("Provide your API key token", hide_input=True)
    if api_key is None:
        if username is None:
            username = click.prompt("Username")
        if password is None:
            password = click.prompt("Password", hide_input=True)

    try:
        # Try to use credentials
        if api_key is None:
            mwdb.login(username, password)
        else:
            # Set API key and check if it's correct
            mwdb.set_api_key(api_key)
            mwdb.api.get("auth/validate")
    except (InvalidCredentialsError, NotAuthenticatedError) as e:
        click.echo("Error: Login failed - {}".format(str(e)), err=True)
        ctx.abort()
    mwdb.api.options.store_credentials()


@main.command("logout")
@pass_mwdb
def logout_command(mwdb):
    """Reset stored credentials"""
    mwdb.api.options.clear_stored_credentials()
