import copy
import json
import tempfile
import unittest
from pathlib import Path

from evals.offline import load_reference_trace, load_trace_file
from evals.trace import TraceError, derive_tool_events


class TraceTests(unittest.TestCase):
    def test_events_are_derived_from_single_message_stream(self):
        _messages, events, _termination, _source = load_reference_trace("zone_2_success")
        self.assertEqual([event.name for event in events], ["verify_carrier", "get_load_context", "record_agreement", "end_call"])
        self.assertEqual(events[2].arguments["agreed_price"], 1700)

    def test_missing_tool_result_is_rejected(self):
        messages, _events, _termination, _source = load_reference_trace("zone_2_success")
        broken = [message for message in copy.deepcopy(messages) if message.get("tool_call_id") != "3"]
        with self.assertRaises(TraceError):
            derive_tool_events(broken)

    def test_mismatched_tool_name_is_rejected(self):
        messages, _events, _termination, _source = load_reference_trace("zone_2_success")
        broken = copy.deepcopy(messages)
        result = next(message for message in broken if message.get("tool_call_id") == "2")
        result["name"] = "record_agreement"
        with self.assertRaises(TraceError):
            derive_tool_events(broken)

    def test_external_trace_cannot_spoof_evidence_source(self):
        messages, _events, termination, _source = load_reference_trace("zone_2_success")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            path.write_text(json.dumps({
                "messages": messages,
                "termination_reason": termination,
                "source": "synthetic_reference_trace",
            }), encoding="utf-8")
            _messages, _events, _termination, source = load_trace_file(path)
        self.assertEqual(source, "external_agent_trace")

    def test_invalid_trace_shape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            path.write_text('{"messages": {}}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_trace_file(path)
