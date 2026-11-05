import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class DatabaseNotReadyError(RuntimeError):
    pass


@contextmanager
def read_only_connection(path: Path) -> Iterator[sqlite3.Connection]:
    if not path.exists():
        raise DatabaseNotReadyError(f"Database not found at {path}. Run `make seed` first.")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
    finally:
        connection.close()
