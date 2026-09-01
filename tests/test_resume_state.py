import base64
import json
import unittest

from resume_state import (
    MAX_RESUME_PAYLOAD_BYTES,
    RESUME_STATE_VERSION,
    decode_resume_state,
    encode_resume_state,
)


class ResumeStateTests(unittest.TestCase):
    def test_round_trip_preserves_json_state(self):
        state = {
            "page": 2,
            "launched": True,
            "activity_answers": {"issue_stock": "Financing"},
            "statement_results": {"Income Statement": True},
        }

        self.assertEqual(decode_resume_state(encode_resume_state(state)), state)

    def test_invalid_tokens_are_ignored(self):
        for token in (None, "", "not-valid-base64!", "a" * 12_001):
            with self.subTest(token=token):
                self.assertIsNone(decode_resume_state(token))

    def test_unknown_version_is_ignored(self):
        payload = json.dumps(
            {"version": RESUME_STATE_VERSION + 1, "state": {"page": 3}}
        ).encode("utf-8")
        token = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

        self.assertIsNone(decode_resume_state(token))

    def test_oversized_state_is_rejected(self):
        with self.assertRaises(ValueError):
            encode_resume_state({"value": "x" * MAX_RESUME_PAYLOAD_BYTES})


if __name__ == "__main__":
    unittest.main()
