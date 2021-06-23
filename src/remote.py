from .methods import MWDBMethods
from .object import MWDBObject


class RemoteAPIClient(object):
    def __init__(self, local_api, remote_name):
        self.local_api = local_api
        self.remote_name = remote_name

    def request(self, method, url, api=True, *args, **kwargs):
        url = (
            "remote/{}/api/{}" if api
            else "remote/{}/{}"
        ).format(self.remote_name, url)
        return self.local_api.request(method, url, *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("delete", *args, **kwargs)


class MWDBRemote(MWDBMethods):
    """
    MWDB object that allows to access the remote instance API

    It has the same methods as :class:`MWDB`, so you can e.g. download a file
    directly from the remote.

    MWDBRemote extends the original interface with :py:meth:`pull_object`/:py:meth:`push_object`
    methods for exchanging objects between instances.
    """

    def __init__(self, api):
        super(MWDBRemote, self).__init__(api=api)

    @property
    def local_api(self):
        return self.api.local_api

    def _pull(self, object_type, object):
        if not isinstance(object, object_type):
            raise TypeError("Argument type must be {}".format(object_type.__name__))
        if object.api is not self.api:
            raise ValueError("Object must be bound with this MWDBRemote instance")
        return object_type.create(
            self.local_api,
            self.api.post(
                "pull/{type}/{id}".format(
                    type=object_type.URL_TYPE,
                    id=object.id
                ), api=False
            )
        )

    def _push(self, object_type, object):
        if not isinstance(object, object_type):
            raise TypeError("Argument type must be {}".format(object_type.__name__))
        if object.api is not self.local_api:
            raise ValueError("Object must be bound with local MWDB instance")
        return object_type.create(
            self.api,
            self.api.post(
                "push/{type}/{id}".format(
                    type=object_type.URL_TYPE,
                    id=object.id
                ), api=False
            )
        )

    def pull_object(self, object):
        """
        Pulls an remote object to the local instance

        .. code-block:: python

            mwdb_cert = mwdb.remote("mwdb.cert.pl")

            # Get file object from mwdb.cert.pl
            remote_file = mwdb_cert.query_file("75dec9b5253ba55a6fecc2e96a704e654785e7d9")

            # Pull that file to the local instance
            local_file = mwdb_cert.pull_file(remote_file)

            # Tag locally with 'feed:cert.pl'
            local_file.add_tag("feed:cert.pl")

        :param object: Remote object
        :type object: MWDBObject
        :return: Pulled MWDBObject bound with local instance
        """
        if not issubclass(type(object), MWDBObject):
            raise TypeError("Argument must be subclass of MWDBObject")
        return self._pull(type(object), object)

    def push_object(self, object):
        """
        Pushes an local object to the remote instance

        .. code-block:: python

             # Get file object from local repository
            local_file = mwdb.query_file("75dec9b5253ba55a6fecc2e96a704e654785e7d9")

            # Push that file to the remote instance
            mwdb_cert = mwdb.remote("mwdb.cert.pl")
            remote_file = mwdb.push_object(local_file)

        :param object: Local object
        :type object: MWDBObject
        :return: Pushed MWDBObject bound with remote instance
        """
        if not issubclass(type(object), MWDBObject):
            raise TypeError("Argument must be subclass of MWDBObject")
        return self._push(type(object), object)
