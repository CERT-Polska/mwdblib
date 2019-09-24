import click
import hashlib


def is_correct_hash(value):
    return all(map(lambda c: c in "0123456789abcdef", value.lower())) and len(value) in [32, 40, 64, 128]


class Hash(click.ParamType):
    """ParamType accepting hashes"""
    def convert(self, value, param, ctx):
        if not is_correct_hash(value):
            self.fail("'%s' is not correct MD5/SHA1/SHA256/SHA512 hash" % value,
                      param, ctx)
        return value.lower()


class HashFile(click.File):
    name = 'file_or_hash'
    """ParamType accepting hashes or evaluating SHA256 for provided file"""
    def __init__(self):
        # We shouldn't want to parametrize this
        super(HashFile, self).__init__(mode='rb')

    def convert(self, value, param, ctx):
        if is_correct_hash(value):
            return value.lower()
        f = super(HashFile, self).convert(value, param, ctx)
        return hashlib.sha256(f.read()).hexdigest()
