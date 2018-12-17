from collections import defaultdict
from functools import wraps


def lazy_property(url_pattern=None):
    def wrapper(f):
        @property
        @wraps(f)
        def wrapped_property(self):
            url = (url_pattern or getattr(self, "URL_PATTERN", None)).format(**self.data)
            property = f.__name__
            mapper = getattr(self, "mapper_{}".format(property), lambda d: d)
            if f(self) is None:
                data = self.api.get(url)
                self._update(mapper(data))
            return f(self)
        return wrapped_property
    return wrapper


class MalwarecageElement(object):
    def __init__(self, api, data):
        self.api = api
        self.data = {}
        self._update(data)

    def _update(self, data):
        self.data.update(data)

    @property
    def id(self):
        return self.data["id"]


class MalwarecageComment(MalwarecageElement):
    def __init__(self, api, data, parent):
        super(MalwarecageComment, self).__init__(api, data)
        self.parent = parent

    @property
    def author(self):
        return self.data["author"]

    @property
    def timestamp(self):
        return self.data["timestamp"]

    @property
    def comment(self):
        return self.data["comment"]

    def delete(self):
        self.api.delete("object/{}/comment/{}".format(self.parent.id, self.id))


class MalwarecageObject(MalwarecageElement):
    URL_PATTERN = "object/{id}"

    @staticmethod
    def create(api, data):
        from .file import MalwarecageFile
        from .config import MalwarecageConfig
        from .blob import MalwarecageBlob
        type = data["type"]
        data = {k: v for k, v in data.items() if k != "type"}
        if type == "file":
            return MalwarecageFile(api, data)
        elif type == "static_config":
            return MalwarecageConfig(api, data)
        elif type == "blob":
            return MalwarecageBlob(api, data)
        else:
            return None

    def mapper_tags(self, data):
        return {"tags": data}

    @lazy_property("object/{id}/tag")
    def tags(self):
        return [t["tag"] for t in self.data["tags"]] if "tags" in self.data else None

    def mapper_comments(self, data):
        return {"comments": data}

    @lazy_property("object/{id}/comment")
    def comments(self):
        return list(map(lambda c: MalwarecageComment(self.api, c, self), self.data["comments"])) \
            if "comments" in self.data else None

    @lazy_property("object/{id}/meta")
    def metakeys(self):
        if "metakeys" not in self.data:
            return None
        result = defaultdict(list)
        for m in self.data["metakeys"]:
            result[m["key"]].append(m["value"])
        return dict(result)

    @lazy_property()
    def upload_time(self):
        import dateutil.parser
        return dateutil.parser.parse(self.data["upload_time"]) if "upload_time" in self.data else None

    @lazy_property()
    def parents(self):
        return list(map(lambda o: MalwarecageObject.create(self.api, o), self.data["parents"])) \
            if "parents" in self.data else None

    @lazy_property()
    def children(self):
        return list(map(lambda o: MalwarecageObject.create(self.api, o), self.data["children"])) \
            if "children" in self.data else None

    def add_tag(self, tag):
        self.api.put("object/{id}/tag".format(**self.data), json={
            "tag": tag
        })
        if "tags" in self.data:
            del self.data["tags"]

    def remove_tag(self, tag):
        self.api.delete("object/{id}/tag".format(**self.data), params={
            "tag": tag
        })
        if "tags" in self.data:
            del self.data["tags"]

    def add_comment(self, comment):
        self.api.post("object/{id}/comment".format(**self.data), json={
            "comment": comment
        })
        if "comments" in self.data:
            del self.data["comments"]

    def add_metakey(self, key, value):
        self.api.post("object/{id}/meta".format(**self.data), json={
            "key": key,
            "value": value
        })

    def flush(self):
        self.data = {"id": self.data["id"]}
