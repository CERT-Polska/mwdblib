import hashlib


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
        return hashlib.sha256(str(obj).encode("utf-8")).hexdigest()
