import datetime
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union, cast

if TYPE_CHECKING:
    from .api import APIClient
    from .comment import MWDBComment
    from .share import MWDBShare

MWDBElementData = Dict[str, Any]
MWDBElementDataMapper = Callable[[MWDBElementData], Any]


class MWDBElement:
    """
    Represents any MWDB entity that can be loaded from API
    """

    def __init__(self, api: "APIClient", data: MWDBElementData) -> None:
        self.api = api
        self.data = dict(data)

    def _load(
        self, url_pattern: str, mapper: Optional[MWDBElementDataMapper] = None
    ) -> None:
        """
        Attribute lazy-loading method.
        """
        data = self.api.get(url_pattern.format(**self.data))
        if mapper is not None:
            data = mapper(data)
        self.data.update(data)

    def _expire(self, key: str) -> None:
        """
        Cached attribute value expiration
        """
        if key in self.data:
            del self.data[key]


class MWDBObject(MWDBElement):
    """
    Represents abstract, generic MWDB object.

    Should never be instantiated directly.

    If you really need to get synthetic instance - use internal
    :py:meth:`create` static method.
    """

    URL_TYPE: str = "object"  # Type name in URL endpoint
    TYPE: str = "object"  # Type name in 'type' object field

    def _load(
        self,
        url_pattern: Optional[str] = None,
        mapper: Optional[MWDBElementDataMapper] = None,
    ) -> None:
        if url_pattern is None:
            url_pattern = self.URL_TYPE + "/{id}"
        return super()._load(url_pattern, mapper=mapper)

    @staticmethod
    def create(api: "APIClient", data: MWDBElementData) -> "MWDBObject":
        """
        Creates specialized MWDBObject subclass instance based on specified ``data``
        """
        from .blob import MWDBBlob
        from .config import MWDBConfig
        from .file import MWDBFile

        type = data["type"]
        if type == MWDBFile.TYPE:
            return MWDBFile(api, data)
        elif type == MWDBConfig.TYPE:
            return MWDBConfig(api, data)
        elif type == MWDBBlob.TYPE:
            return MWDBBlob(api, data)
        raise RuntimeError(f"Unsupported object type: '{type}'")

    @property
    def id(self) -> str:
        """
        Object identifier (sha256)
        """
        return cast(str, self.data["id"])

    @property
    def object_type(self) -> str:
        """
        Object type ('file', 'static_config' or 'text_blob')
        """
        return cast(str, self.data["type"])

    @property
    def sha256(self) -> str:
        """
        Object identifier (sha256)
        """
        return self.id

    @property
    def tags(self) -> List[str]:
        """
        Returns list of tags

        :return: List of tags
        """
        if "tags" not in self.data:
            self._load("object/{id}/tag", mapper=lambda data: {"tags": data})
        return [t["tag"] for t in self.data["tags"]]

    @property
    def comments(self) -> List["MWDBComment"]:
        """
        Returns list of comments

        :return: List of comment objects

        Example - print all comments of last object commented as "malware":

        .. code-block:: python

            comments = next(mwdb.search_files('comment:"*malware*"')).comments
            for comment in comments:
                print("{} {}".format(comment.author, comment.comment))
        """
        from .comment import MWDBComment

        if "comments" not in self.data:
            self._load("object/{id}/comment", mapper=lambda data: {"comments": data})
        return [
            MWDBComment(self.api, comment, self) for comment in self.data["comments"]
        ]

    @property
    def shares(self) -> List["MWDBShare"]:
        """
        Returns list of shares

        :return: List of share objects
        """
        from .share import MWDBShare

        if "shares" not in self.data:
            self._load(
                "object/{id}/share",
                mapper=lambda data: {"shares": data.get("shares", [])},
            )
        return [MWDBShare(self.api, share, self) for share in self.data["shares"]]

    @property
    def metakeys(self) -> Dict[str, List[str]]:
        """
        Returns dict object with metakeys.

        :return: Dict object containing metakey attributes
        """
        if "metakeys" not in self.data:
            self._load("object/{id}/meta")
        result = defaultdict(list)
        for m in self.data["metakeys"]:
            result[m["key"]].append(m["value"])
        return dict(result)

    @property
    def upload_time(self) -> "datetime.datetime":
        """
        Returns timestamp of first object upload

        :return: datetime object with object upload timestamp
        """
        if "upload_time" not in self.data:
            self._load()
        return datetime.datetime.fromisoformat(self.data["upload_time"])

    @property
    def parents(self) -> List["MWDBObject"]:
        """
        Returns list of parent objects

        :return: List of parent objects
        """
        if "parents" not in self.data:
            self._load()
        return [self.create(self.api, parent) for parent in self.data["parents"]]

    @property
    def children(self) -> List["MWDBObject"]:
        """
        Returns list of child objects

        :return: List of child objects
        """
        if "children" not in self.data:
            self._load()
        return [self.create(self.api, child) for child in self.data["children"]]

    @property
    def content(self) -> bytes:
        """
        Returns stringified contents of object

        .. versionadded:: 3.0.0
           Added :py:attr:`MWDBObject.content` property
        """
        raise NotImplementedError()

    def add_child(self, child: Union["MWDBObject", str]) -> None:
        """
        Adds reference to child with current object as parent

        :param child: Object or object identifier (sha256)
        :type child: MWDBObject or str
        """
        if not isinstance(child, str):
            child = child.id
        self.api.put(
            "object/{parent}/child/{child}".format(parent=self.id, child=child)
        )
        self._expire("children")

    def add_tag(self, tag: str) -> None:
        """
        Tags object using specified tag

        :param tag: Tag string
        :type tag: str
        """
        self.api.put("object/{id}/tag".format(**self.data), json={"tag": tag})
        self._expire("tags")

    def remove_tag(self, tag: str) -> None:
        """
        Untags object using specified tag

        :param tag: Tag string
        :type tag: str
        """
        self.api.delete("object/{id}/tag".format(**self.data), params={"tag": tag})
        self._expire("tags")

    def add_comment(self, comment: str) -> None:
        """
        Adds comment

        :param comment: Comment string
        :type comment: str
        """
        self.api.post(
            "object/{id}/comment".format(**self.data), json={"comment": comment}
        )
        self._expire("comments")

    def add_metakey(self, key: str, value: str) -> None:
        """
        Adds metakey attribute

        :param key: Attribute key
        :type key: str
        :param value: Attribute value
        :type value: str
        """
        self.api.post(
            "object/{id}/meta".format(**self.data), json={"key": key, "value": value}
        )
        self._expire("metakeys")

    def share_with(self, group: str) -> None:
        """
        Share object with specified group

        .. versionadded:: 3.0.0
           Added :py:meth:`MWDBObject.share_with` method

        :param group: Group name
        :type group: str
        """
        self.api.put("object/{id}/share".format(**self.data), json={"group": group})
        self._expire("shares")

    def flush(self) -> None:
        """
        Flushes local object state in case of pending updates.
        All object-specific properties will be lazy-loaded using API
        """
        self.data = {"id": self.data["id"]}