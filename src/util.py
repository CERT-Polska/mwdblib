import hashlib
import sys


def config_dhash(obj):
    """ Compute a data hash from the object. This is the hashing algorithm
    used internally by malwarecage to assign unique ids to configs
    """
    if isinstance(obj, list):
        return config_dhash(str(sorted([config_dhash(o) for o in obj])))
    elif isinstance(obj, dict):
        return config_dhash(
            [[o, config_dhash(obj[o])] for o in sorted(obj.keys())]
        )
    else:
        obj = str(obj)
        if sys.version_info[0] == 3:
            obj = bytes(obj, "utf-8")
        return hashlib.sha256(obj).hexdigest()
