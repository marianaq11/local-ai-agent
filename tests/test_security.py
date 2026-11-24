import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from security import Rejected
from tools import execute


class BoundaryTests(unittest.TestCase):
    def test_file_allowlist(self):
        for path in ("../agent.py", "/etc/passwd", "something.log", "data/sample_auth.log"):
            with self.subTest(path=path), self.assertRaises(Rejected):
                execute("read_file", {"file": path})

    def test_links_and_large_files(self):
        with tempfile.TemporaryDirectory() as tmp, patch("security.DATA", Path(tmp)):
            sample = Path(tmp) / "sample_auth.log"
            sample.symlink_to(__file__)
            with self.assertRaises(Rejected):
                execute("read_file", {"file": sample.name})
            sample.unlink()
            sample.write_bytes(b"x" * 2049)
            with self.assertRaises(Rejected):
                execute("read_file", {"file": sample.name})

    def test_registry_schema(self):
        for name, args in [
            ("shell", {"cmd": "noop"}), ([], {}), ("log_stats", []), ("read_file", {}),
            ("log_stats", {"file": True}), ("read_file", {"file": "sample_auth.log", "x": 1}),
            ("search_entries", {"file": "sample_auth.log", "query": " "}),
            ("search_entries", {"file": "sample_auth.log", "query": "x" * 101}),
        ]:
            with self.subTest(name=name, args=args), self.assertRaises(Rejected):
                execute(name, args)
