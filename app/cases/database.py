"""Share a transaction across the existing case engines when requested."""
from contextlib import contextmanager, closing


@contextmanager
def case_connection(connect, connection=None):
    if connection is not None:
        yield connection
        return
    with closing(connect()) as owned, owned:
        yield owned
