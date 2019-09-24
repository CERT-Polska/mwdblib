import click
import humanize


class AttributeFormatter(object):
    def format(self, formatter, value):
        return value


class BoldFormatter(AttributeFormatter):
    def format(self, formatter, value):
        if formatter.colorize:
            return click.style(value, bold=True)
        else:
            return value


class TagFormatter(AttributeFormatter):
    @staticmethod
    def get_tag_color(tag):
        tag_colors = {
            "bright_blue": ["spam", "suspicious", "unwanted", "apk", "pexe", "zip", "archive", "src:", "uploader:",
                            "feed:"],
            "bright_yellow": ["ripped:", "contains:", "matches:"],
            "bright_green": ["static:", "dynamic:"],
            "red": ["runnable:", "archive:", "dump:", "script:"]
        }
        for color, predecessors in tag_colors.items():
            for predecessor in predecessors:
                if tag.startswith(predecessor):
                    return color
        if ":" in tag:
            return "blue"
        return "bright_red"

    def format(self, formatter, value):
        if not value:
            return "<none>"
        if formatter.colorize:
            return " ".join(click.style(tag, fg=TagFormatter.get_tag_color(tag)) for tag in value)
        else:
            return " ".join(tag for tag in value)


class SizeFormatter(AttributeFormatter):
    def format(self, formatter, value):
        if formatter.humanize:
            return humanize.naturalsize(value)
        else:
            return value


class DateFormatter(AttributeFormatter):
    def format(self, formatter, value):
        if formatter.humanize:
            return humanize.naturaldate(value.replace(tzinfo=None))
        else:
            return value.isoformat()


class ObjectTypeFormatter(AttributeFormatter):
    @staticmethod
    def normalize_type(type):
        if type == "static_config":
            return "config"
        elif type == "text_blob":
            return "blob"
        return type

    def format(self, formatter, value):
        type_colors = {
            "file": "bright_red",
            "config": "bright_green",
            "blob": "bright_blue"
        }
        value = ObjectTypeFormatter.normalize_type(value)
        if formatter.colorize:
            return click.style(value, fg=type_colors.get(value))
        else:
            return value


class RelationTagFormatter(TagFormatter):
    def format(self, formatter, value):
        tags = set([tag for object in value for tag in object.tags])
        return super(RelationTagFormatter, self).format(formatter, list(tags))
