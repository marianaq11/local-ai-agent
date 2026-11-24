"""The approved dataset is deliberately small enough to inspect in full."""
import os
import stat

from config import DATA, FILES


class Rejected(ValueError):
    """An action failed validation before its result could reach the model."""


def read_sample(filename):
    if filename not in FILES:
        raise Rejected("Choose an approved sample filename.")
    # Anchor the lookup to a directory descriptor. Reject symlinks at both
    # levels, including a link swapped in between validation and opening.
    try:
        directory = os.open(DATA, os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=directory)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise Rejected("Sample must be a regular file.")
                raw = stream.read(2049)
        finally:
            os.close(directory)
        if len(raw) > 2048:
            raise Rejected("Sample exceeds the teaching dataset size limit.")
        return raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise Rejected("Sample unavailable or invalid.") from error
