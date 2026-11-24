import json
import unittest
from unittest.mock import Mock, patch

import requests

from agent import run
from config import DEMO

TOOL = '{"tool":"log_stats","args":{"file":"sample_auth.log"}}'
FINAL = '{"final":"Four failures appeared in the sample."}'


def response(content):
    return Mock(status_code=200, **{"json.return_value": {"message": {"content": content}}})


class AgentTests(unittest.TestCase):
    def setUp(self):
        patcher = patch("requests.Session.post", autospec=True)
        self.post = patcher.start()
        self.addCleanup(patcher.stop)

    def script(self, *texts):
        self.post.side_effect = [response(text) for text in texts]

    def test_context_and_independent_judge(self):
        self.script(TOOL, "YES", FINAL, "YES")
        record = run(DEMO)
        self.assertEqual((record["status"], record["iterations"]), ("completed", 2))
        self.assertEqual(record["final_output"], json.loads(FINAL)["final"])
        self.assertEqual(len(record["tool_requests"]), 1)
        actor, judge, next_actor, final_judge = self.post.call_args_list
        for call in self.post.call_args_list:
            self.assertEqual(call.args[1], "http://127.0.0.1:11434/api/chat")
            self.assertFalse(call.args[0].trust_env)
            self.assertFalse(call.kwargs["allow_redirects"])
            self.assertIn("timeout", call.kwargs)
        self.assertEqual(actor.kwargs["json"]["format"], "json")
        self.assertNotIn("format", judge.kwargs["json"])
        messages = next_actor.kwargs["json"]["messages"]
        self.assertEqual([m["role"] for m in messages], ["system", "user", "assistant", "user"])
        self.assertEqual(messages[1]["content"], DEMO)
        self.assertEqual(json.loads(messages[-1]["content"])["untrusted_tool_result"]["failures"], 4)
        judged = json.loads(final_judge.kwargs["json"]["messages"][-1]["content"])
        self.assertEqual(judged["original_task"], DEMO)
        self.assertEqual(judged["transcript"][-2]["content"], FINAL)

    def test_no_or_malformed_verdict_continues(self):
        self.script(TOOL, "NO", FINAL, "YES probably", FINAL, "NO", FINAL, "YES")
        report = run(DEMO)
        self.assertEqual(report["verdicts"], ["NO", "INVALID", "NO", "YES"])
        self.assertEqual(report["status"], "completed")

    def test_incomplete_at_default_limit(self):
        self.script(*([FINAL, "YES"] * 5))
        report = run(DEMO)
        self.assertEqual(report["status"], "iteration_limit")
        self.assertEqual(report["iterations"], 5)
        self.assertEqual(self.post.call_count, 10)

    def test_bad_json_and_unauthorized_action(self):
        self.script("not json", "YES", '{"tool":"exec","args":{}}', "YES")
        report = run(DEMO, limit=2)
        self.assertEqual(report["status"], "iteration_limit")
        self.assertEqual(report["rejected_tool_requests"], 1)
        self.assertEqual(report["tool_requests"][0]["rejection"], "Unknown tool.")
        self.assertEqual(report["final_output"], "")

    def test_duplicate_fields_are_rejected_before_dispatch(self):
        self.script('{"tool":"other","tool":"log_stats","args":{"file":"sample_auth.log"}}', "YES")
        report = run(DEMO, limit=1)
        self.assertEqual(report["tool_requests"], [])
        self.assertEqual(report["status"], "iteration_limit")

    def test_connection_and_timeout_failures(self):
        for error in (requests.ConnectionError(), requests.Timeout()):
            self.post.side_effect = error
            self.assertEqual(run(DEMO)["status"], "model_error")

    def test_evaluator_connection_failure(self):
        self.post.side_effect = [response(TOOL), requests.Timeout()]
        report = run(DEMO)
        self.assertEqual(report["status"], "model_error")
        self.assertEqual(report["iterations"], 1)

    def test_bad_http_status_body_and_envelope(self):
        for reply in (Mock(status_code=307), Mock(status_code=404),
                      Mock(status_code=200, **{"json.side_effect": ValueError()}),
                      Mock(status_code=200, **{"json.return_value": []}), response(None)):
            self.post.return_value = reply
            self.assertEqual(run(DEMO)["status"], "model_error")
