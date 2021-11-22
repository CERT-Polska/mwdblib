import functools

import click

from .json import JSONFormatter
from .short import ShortFormatter
from .tabular import TabularFormatter

formatters = {"table": TabularFormatter, "short": ShortFormatter, "json": JSONFormatter}


def get_formatter(options):
    default_formatter_class = TabularFormatter
    formatter_class = default_formatter_class
    for option in options:
        if option in formatters:
            formatter_class = formatters[option]
            break
    return formatter_class(
        colorize=("nocolor" not in options),
        humanize=("nohuman" not in options),
        pager=("nopager" not in options),
    )


def pass_formatter(fn):
    @click.option(
        "--output",
        "-o",
        type=click.Choice(["nocolor", "nohuman", "nopager", *formatters.keys()]),
        default=[],
        multiple=True,
        help="Format options",
    )
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        output_options = kwargs.pop("output")
        formatter = get_formatter(output_options)
        return fn(formatter=formatter, *args, **kwargs)

    return wrapper


def confirm_action(fn):
    @functools.wraps(fn)
    @pass_formatter
    def wrapper(*args, **kwargs):
        formatter = kwargs["formatter"]
        del kwargs["formatter"]
        result = fn(*args, **kwargs)
        formatter.print_confirmation(**result)
        return result

    return wrapper
