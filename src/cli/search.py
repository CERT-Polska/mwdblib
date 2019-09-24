import click
from itertools import islice

from click_default_group import DefaultGroup

from .authenticator import pass_mwdb
from .main import main
from .formatters import pass_formatter


@main.group("search", cls=DefaultGroup, default='files', default_if_no_args=True)
def search_command():
    """
    Search objects using Lucene query
    """
    pass


@search_command.command("objects")
@click.argument("query")
@click.option("--limit", "-n", default=200)
@pass_formatter
@pass_mwdb
def search_objects(mwdb, formatter, query, limit):
    """
    Search objects of all types
    """
    recent = islice(mwdb.search(query), limit)
    formatter.print_list(recent, formatter.format_object_list)


@search_command.command("files")
@click.argument("query")
@click.option("--limit", "-n", default=200)
@pass_formatter
@pass_mwdb
def search_files(mwdb, formatter, query, limit):
    """
    Search files
    """
    recent = islice(mwdb.search_files(query), limit)
    formatter.print_list(recent, formatter.format_file_list)


@search_command.command("configs")
@click.argument("query")
@click.option("--limit", "-n", default=200)
@pass_formatter
@pass_mwdb
def search_configs(mwdb, formatter, query, limit):
    """
    Search configs
    """
    recent = islice(mwdb.search_configs(query), limit)
    formatter.print_list(recent, formatter.format_config_list)


@search_command.command("blobs")
@click.argument("query")
@click.option("--limit", "-n", default=200)
@pass_formatter
@pass_mwdb
def search_blobs(mwdb, formatter, query, limit):
    """
    Search blobs
    """
    recent = islice(mwdb.search_blobs(query), limit)
    formatter.print_list(recent, formatter.format_blob_list)
