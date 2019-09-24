import click
import functools

from .short import ShortFormatter
from .tabular import TabularFormatter


def get_formatter(output_format):
    formatter_classes = {
        "table": TabularFormatter,
        "short": ShortFormatter
    }
    output_format = output_format.lstrip("=").split(",")
    formatter_class = TabularFormatter
    for class_str in formatter_classes.keys():
        if class_str in output_format:
            formatter_class = formatter_classes[class_str]
    return formatter_class(
        colorize=("nocolor" not in output_format),
        humanize=("nohuman" not in output_format),
        pager=("nopager" not in output_format))


def pass_formatter(fn):
    @functools.wraps(fn)
    @click.option("--output", "-o", default="",
                  help="Format attributes separated by commas. Supported values: nocolor, "
                       "nopager, nohuman")
    def wrapper(*args, **kwargs):
        formatter = get_formatter(output_format=kwargs["output"])
        del kwargs["output"]
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
