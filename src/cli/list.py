import click
from itertools import islice

from click_default_group import DefaultGroup

from .authenticator import pass_mwdb
from .main import main
from .formatters import pass_formatter


@main.group("list", cls=DefaultGroup, default='files', default_if_no_args=True)
def list_command():
    """
    List recent objects
    """
    pass


@list_command.command("objects")
@click.option("--limit", "-n", default=200)
@pass_formatter
@pass_mwdb
def list_objects(mwdb, formatter, limit):
    """
    List recent objects of all types
    """
    recent = islice(mwdb.recent_objects(), limit)
    formatter.print_list(recent, formatter.format_object_list)


@list_command.command("files")
@click.option("--limit", "-n", default=200)
@pass_formatter
@pass_mwdb
def list_files(mwdb, formatter, limit):
    """
    List recent files
    """
    recent = islice(mwdb.recent_files(), limit)
    formatter.print_list(recent, formatter.format_file_list)


@list_command.command("configs")
@click.option("--limit", "-n", default=200)
@pass_formatter
@pass_mwdb
def list_configs(mwdb, formatter, limit):
    """
    List recent configs
    """
    recent = islice(mwdb.recent_configs(), limit)
    formatter.print_list(recent, formatter.format_config_list)


@list_command.command("blobs")
@click.option("--limit", "-n", default=200)
@pass_formatter
@pass_mwdb
def list_blobs(mwdb, formatter, limit):
    """
    List recent blobs
    """
    recent = islice(mwdb.recent_blobs(), limit)
    formatter.print_list(recent, formatter.format_blob_list)
