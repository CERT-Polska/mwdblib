import click
from keyring.errors import NoKeyringError

from ..exc import InvalidCredentialsError, NotAuthenticatedError
from .main import main, pass_mwdb


@main.command("login")
@click.option(
    "--username", "-u", type=str, default=None, help="MWDB user name (default: ask)"
)
@click.option(
    "--password", "-p", type=str, default=None, help="MWDB password (default: ask)"
)
@click.option(
    "--use-keyring/--no-keyring",
    default=None,
    help="Don't use keyring, store credentials in plaintext",
)
@click.option("--via-api-key", "-A", is_flag=True, help="Use API key provided by stdin")
@click.option(
    "--api-key",
    "-a",
    type=str,
    default=None,
    help="API key token (default: password-based authentication)",
)
@pass_mwdb(autologin=False)
@click.pass_context
def login_command(ctx, mwdb, username, password, use_keyring, via_api_key, api_key):
    """Store credentials for MWDB authentication"""
    if via_api_key:
        api_key = click.prompt("Provide your API key token", hide_input=True)

    if api_key is None:
        if username is None:
            username = click.prompt("Username")
        if password is None:
            password = click.prompt("Password", hide_input=True)

    if use_keyring is not None:
        mwdb.api.options.use_keyring = use_keyring

    try:
        # Try to use credentials
        if api_key is None:
            mwdb.login(username, password)
        else:
            # Set API key and check if it's correct
            mwdb.api.set_api_key(api_key)
            mwdb.api.get("auth/validate")
    except (InvalidCredentialsError, NotAuthenticatedError) as e:
        click.echo("Error: Login failed - {}".format(str(e)), err=True)
        ctx.abort()
    try:
        mwdb.api.options.store_credentials(username, password, api_key)
    except NoKeyringError:
        click.echo(
            "Failed to login! Keyring is not available on this system. "
            "See https://pypi.org/project/keyring for details, or use the (insecure) "
            "--no-keyring option.",
            err=True,
        )
        ctx.abort()
    if not mwdb.api.options.use_keyring:
        click.echo(
            f"Warning! Your password is stored in plaintext in "
            f"{mwdb.api.options.config_path}. Use --use-keyring to store "
            f"credentials in keyring (if available on your system).",
            err=True,
        )
    click.echo(
        f"Logged in successfully to {mwdb.api.options.api_url} "
        f"as {mwdb.api.logged_user}",
        err=True,
    )


@main.command("logout")
@pass_mwdb(autologin=False)
def logout_command(mwdb):
    """Reset stored credentials"""
    if mwdb.api.options.clear_stored_credentials():
        click.echo(f"Logged out successfully from {mwdb.api.options.api_url}", err=True)
    else:
        click.echo(
            f"Error: user already logged out from {mwdb.api.options.api_url}!", err=True
        )
