import json

from .abstract import ObjectFormatter


class JSONFormatter(ObjectFormatter):
    def format_object_list(self, objects):
        for obj in objects:
            yield json.dumps(obj.data)

    def format_file_detailed(self, file):
        return json.dumps(file.data)

    def format_config_detailed(self, config):
        return json.dumps(config.data)

    def format_blob_detailed(self, blob):
        return json.dumps(blob.data)

    def format_shares_list(self, shares):
        for share in shares:
            yield json.dumps(share.data)

    def format_comments_list(self, comments):
        for comment in comments:
            yield json.dumps(comment.data)

    def format_metakeys_list(self, metakeys):
        return json.dumps(metakeys)

    def format_attributes_list(self, attributes):
        return json.dumps(attributes)
