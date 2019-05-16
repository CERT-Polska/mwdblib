from collections import defaultdict
from functools import wraps


class PropertyUnloaded(RuntimeError):
    pass


def lazy_property(url_pattern=None, nullable=False):
    def wrapper(f):
        @property
        @wraps(f)
        def wrapped_property(self):
            url = (url_pattern or getattr(self, "URL_PATTERN", None)).format(**self.data)
            property = f.__name__
            mapper = getattr(self, "mapper_{}".format(property), lambda d: d)
            try:
                result = f(self)
                if result is None and not nullable:
                    raise PropertyUnloaded()
                return result
            except PropertyUnloaded:
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


class MalwarecageObject(MalwarecageElement):
    """
    Represents abstract, generic Malwarecage object.

    Should never be instantiated directly.

    If you really need to get synthetic instance - use internal :py:meth:`create` static method.
    """
    URL_PATTERN = "object/{id}"

    def _update(self, data):
        from .config import MalwarecageConfig
        if "config" not in data:
            data = dict(data)
            if "latest_config" in data and data["latest_config"]:
                data["config"] = MalwarecageConfig(self.api, data["latest_config"])
            elif "children" in data:
                """
                If there are children but no latest_config: probably API is in old version
                Try to emulate
                """
                config = next((child for child in data["children"] if child["type"] == "static_config"), None)
                data["config"] = config and MalwarecageConfig(self.api, config)
        super(MalwarecageObject, self)._update(data)

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

    @property
    def sha256(self):
        """
        Object identifier (sha256)
        """
        return self.id

    def mapper_tags(self, data):
        return {"tags": data}

    @lazy_property("object/{id}/tag")
    def tags(self):
        """
        Returns list of tags

        :rtype: list[str]
        :return: List of tags
        """
        return [t["tag"] for t in self.data["tags"]] if "tags" in self.data else None

    def mapper_comments(self, data):
        return {"comments": data}

    @lazy_property("object/{id}/comment")
    def comments(self):
        """
        Returns list of comments

        :rtype: list[:class:`mwdblib.comment.MalwarecageComment`]
        :return: List of comment objects

        Example - print all comments of last object commented as "malware":

        .. code-block:: python

            comments = next(mwdb.search_files('comment:"*malware*"')).comments
            for comment in comments:
                print("{} {}".format(comment.author, comment.comment))
        """
        from .comment import MalwarecageComment
        return list(map(lambda c: MalwarecageComment(self.api, c, self), self.data["comments"])) \
            if "comments" in self.data else None

    def mapper_shares(self, data):
        return {"shares": data.get("shares", [])}

    @lazy_property("object/{id}/share")
    def shares(self):
        """
        Returns list of shares

        :rtype: list[:class:`mwdblib.share.MalwarecageShare`]
        :return: List of share objects
        """
        from .share import MalwarecageShare
        return list(map(lambda s: MalwarecageShare(self.api, s, self), self.data["shares"])) \
            if "shares" in self.data else None

    @lazy_property("object/{id}/meta")
    def metakeys(self):
        """
        Returns dict object with metakeys.

        :rtype: dict
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

        :rtype: :class:`datetime.datetime`
        :return: datetime object with object upload timestamp
        """
        import dateutil.parser
        return dateutil.parser.parse(self.data["upload_time"]) if "upload_time" in self.data else None

    @lazy_property()
    def parents(self):
        """
        Returns list of parent objects

        :rtype: List[:class:`MalwarecageObject`]
        :return: List of parent objects
        """
        return list(map(lambda o: MalwarecageObject.create(self.api, o), self.data["parents"])) \
            if "parents" in self.data else None

    @lazy_property()
    def children(self):
        """
        Returns list of child objects

        :rtype: List[:class:`MalwarecageObject`]
        :return: List of child objects
        """
        return list(map(lambda o: MalwarecageObject.create(self.api, o), self.data["children"])) \
            if "children" in self.data else None

    @lazy_property(nullable=True)
    def config(self):
        """
        Returns latest config related with this object

        :rtype: :class:`MalwarecageConfig` or None
        :return: Latest configuration if found
        """
        if "config" not in self.data:
            raise PropertyUnloaded()
        return self.data["config"]

    def add_child(self, child):
        """
        Adds reference to child with current object as parent

        :param child: Object or object identifier (sha256)
        :type child: MalwarecageObject or str
        """
        if not isinstance(child, str):
            child = child.id
        self.api.put("object/{parent}/child/{child}".format(parent=self.id, child=child))
        if "children" in self.data:
            del self.data["children"]

    def add_tag(self, tag):
        """
        Tags object using specified tag

        :param tag: Tag string
        :type tag: str
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
        :type tag: str
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
        :type comment: str
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
        :type key: str
        :param value: Attribute value
        :type value: str
        """
        self.api.post("object/{id}/meta".format(**self.data), json={
            "key": key,
            "value": value
        })

    def flush(self):
        """
        Flushes local object state in case of pending updates.
        All object-specific properties will be lazy-loaded using API
        """
        self.data = {"id": self.data["id"]}
