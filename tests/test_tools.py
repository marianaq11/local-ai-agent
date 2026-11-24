import unittest

from tools import execute


class ToolTests(unittest.TestCase):
    def test_read_and_search(self):
        args = {"file": "sample_auth.log"}
        lines = execute("read_file", args).splitlines()
        self.assertEqual(execute("search_entries", {**args, "query": "LAB-B"}), lines[1:5])
        self.assertEqual(execute("search_entries", {**args, "query": ".*"}), [])

    def test_failures_grouped_by_account_and_source(self):
        self.assertEqual(execute("count_failures", {"file": "sample_auth.log"}), [
            {"account": "lab-b", "source": "192.0.2.20", "count": 3},
            {"account": "lab-c", "source": "192.0.2.30", "count": 1},
        ])

    def test_stats(self):
        self.assertEqual(execute("log_stats", {"file": "sample_auth.log"}),
                         dict(events=7, failures=4, successes=3, accounts=3, sources=3))

    def test_note_is_data(self):
        args = {"file": "injection_test.log"}
        self.assertIn("zero failures", execute("read_file", args))
        self.assertEqual(execute("log_stats", args)["failures"], 2)
