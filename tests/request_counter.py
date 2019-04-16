from requests import Session


class RequestCountMismatchException(Exception):
    pass


class RequestsCounter:
    def __init__(self, expect_requests):
        self.monkey_patch = None
        self.expect_requests = expect_requests
        self.counter = 0

    def __enter__(self):
        def wrap(*args, **kwargs):
            self.counter += 1
            return self.monkey_patch(*args, **kwargs)

        self.monkey_patch = Session.request
        Session.request = wrap

    def __exit__(self, type, value, traceback):
        Session.request = self.monkey_patch
        if self.counter != self.expect_requests:
            raise RequestCountMismatchException(
                self.counter,
                self.expect_requests
            )
