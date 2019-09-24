import click

from . import main
from .authenticator import MwdbAuthenticator
from ..exc import InvalidCredentialsError


@main.command("login")
@click.option("--username", "-u", type=str, default=None,
              help="Malwarecage user name (default: ask)")
@click.option("--password", "-p", type=str, default=None,
              help="Malwarecage password (default: ask)")
@click.option("--via-api-key", "-A", is_flag=True)
@click.option("--api-key", "-a", type=str, default=None,
              help="API key token (default: password-based authentication)")
@click.pass_context
def login_command(ctx, username, password, via_api_key, api_key):
    """Setup credentials for Malwarecage authentication"""
    if via_api_key:
        api_key = click.prompt("Provide your API key token", hide_input=True)
    if api_key is None:
        if username is None:
            username = click.prompt("Username")
        if password is None:
            password = click.prompt("Password", hide_input=True)
    authenticator = MwdbAuthenticator()
    authenticator.store_login(username, password, api_key)
    try:
        mwdb = authenticator.get_authenticated_mwdb(ctx.obj.get("api_url", None))
        # todo: Find more appropriate way to check successful authentication
        mwdb.query("", raise_not_found=False)
    except InvalidCredentialsError:
        click.echo("Error: Login failed - invalid credentials.", err=True)
        authenticator.reset_login()
        ctx.abort()


@main.command("logout")
def logout_command():
    """Reset stored credentials"""
    authenticator = MwdbAuthenticator()
    authenticator.reset_login()
