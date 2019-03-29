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
        """
        Object identifier (sha256)
        """
        return self.data["id"]

    @property
    def sha256(self):
        return self.id


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
    """
    Represents generic Malwarecage object
    """
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
        elif type == "text_blob":
            return MalwarecageBlob(api, data)
        else:
            return None

    def mapper_tags(self, data):
        return {"tags": data}

    @lazy_property("object/{id}/tag")
    def tags(self):
        """
        Returns list of tags
        :return: List of tags
        """
        return [t["tag"] for t in self.data["tags"]] if "tags" in self.data else None

    def mapper_comments(self, data):
        return {"comments": data}

    @lazy_property("object/{id}/comment")
    def comments(self):
        """
        Returns list of comments
        :return: List of comment objects
        """
        return list(map(lambda c: MalwarecageComment(self.api, c, self), self.data["comments"])) \
            if "comments" in self.data else None

    @lazy_property("object/{id}/meta")
    def metakeys(self):
        """
        Returns dict object with metakeys.
        :return: Dict object containing metakey attributes
        """
        if "metakeys" not in self.data:
            return None
        result = defaultdict(list)
        for m in self.data["metakeys"]:
            result[m["key"]].append(m["value"])
        return dict(result)

    @lazy_property()
    def upload_time(self):
        """
        Returns timestamp of first object upload
        :return: datetime object with object upload timestamp
        """
        import dateutil.parser
        return dateutil.parser.parse(self.data["upload_time"]) if "upload_time" in self.data else None

    @lazy_property()
    def parents(self):
        """
        Returns list of parent objects
        :return: List of parent objects
        """
        return list(map(lambda o: MalwarecageObject.create(self.api, o), self.data["parents"])) \
            if "parents" in self.data else None

    @lazy_property()
    def children(self):
        """
        Returns list of child objects
        :return: List of child objects
        """
        return list(map(lambda o: MalwarecageObject.create(self.api, o), self.data["children"])) \
            if "children" in self.data else None

    def add_child(self, child):
        """
        Adds reference to child with current object as parent
        :param child: MalwarecageObject object
        """
        self.api.put("object/{parent}/child/{child}".format(parent=self.id, child=child.id))
        if "children" in self.data:
            del self.data["children"]

    def add_tag(self, tag):
        """
        Tags object using specified tag
        :param tag: Tag string
        """
        self.api.put("object/{id}/tag".format(**self.data), json={
            "tag": tag
        })
        if "tags" in self.data:
            del self.data["tags"]

    def remove_tag(self, tag):
        """
        Untags object using specified tag
        :param tag: Tag string
        """
        self.api.delete("object/{id}/tag".format(**self.data), params={
            "tag": tag
        })
        if "tags" in self.data:
            del self.data["tags"]

    def add_comment(self, comment):
        """
        Adds comment
        :param comment: Comment string
        """
        self.api.post("object/{id}/comment".format(**self.data), json={
            "comment": comment
        })
        if "comments" in self.data:
            del self.data["comments"]

    def add_metakey(self, key, value):
        """
        Adds metakey attribute
        :param key: Attribute key
        :param value: Attribute value
        """
        self.api.post("object/{id}/meta".format(**self.data), json={
            "key": key,
            "value": value
        })

    def flush(self):
        """
        Flushes local object state.
        All object-specific properties will be lazy-loaded using API
        """
        self.data = {"id": self.data["id"]}
