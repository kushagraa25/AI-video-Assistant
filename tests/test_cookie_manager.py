"""
Tests for Cookie Manager module and hidden route helpers.
"""

import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.cookie_manager import (
    parse_cookie_lines,
    save_cookie_content,
    get_cookie_status,
    delete_cookie_files,
    get_active_cookie_file,
    get_cookie_target_path,
)
from backend.audio_processor import get_cookie_file


class TestCookieManager(unittest.TestCase):

    def setUp(self):
        # Clean any existing test cookies
        delete_cookie_files()

    def tearDown(self):
        delete_cookie_files()

    def test_parse_cookie_lines(self):
        sample_netscape = (
            "# Netscape HTTP Cookie File\n"
            "# Comment line\n"
            ".youtube.com\tTRUE\t/\tTRUE\t1893456000\tVISITOR_INFO1_LIVE\tsample_visitor_token\n"
            "#HttpOnly_.youtube.com\tTRUE\t/\tTRUE\t1893456000\tLOGIN_INFO\tsample_login_token\n"
            "example.com\tFALSE\t/test\tFALSE\t0\tcustom_cookie\tcustom_val\n"
        )
        cookies = parse_cookie_lines(sample_netscape)
        self.assertEqual(len(cookies), 3)

        # Check first cookie
        self.assertEqual(cookies[0]["name"], "VISITOR_INFO1_LIVE")
        self.assertEqual(cookies[0]["domain"], ".youtube.com")
        self.assertTrue(cookies[0]["is_youtube"])
        self.assertFalse(cookies[0]["http_only"])

        # Check second cookie (#HttpOnly_)
        self.assertEqual(cookies[1]["name"], "LOGIN_INFO")
        self.assertTrue(cookies[1]["http_only"])
        self.assertTrue(cookies[1]["is_youtube"])

        # Check third cookie (non-YouTube)
        self.assertEqual(cookies[2]["name"], "custom_cookie")
        self.assertFalse(cookies[2]["is_youtube"])

    def test_save_and_get_status(self):
        raw_cookie = (
            ".youtube.com\tTRUE\t/\tTRUE\t1893456000\tVISITOR_INFO1_LIVE\tsample_visitor\n"
            ".youtube.com\tTRUE\t/\tTRUE\t1893456000\tLOGIN_INFO\tsample_login\n"
        )
        success, msg, count = save_cookie_content(raw_cookie)
        self.assertTrue(success)
        self.assertEqual(count, 2)

        status = get_cookie_status()
        self.assertTrue(status["exists"])
        self.assertEqual(status["total_cookies"], 2)
        self.assertEqual(status["youtube_cookies"], 2)
        self.assertIn("VISITOR_INFO1_LIVE", status["key_cookies_present"])
        self.assertIn("LOGIN_INFO", status["key_cookies_present"])

        # audio_processor.get_cookie_file() should pick it up automatically
        cookie_path = get_cookie_file()
        self.assertIsNotNone(cookie_path)
        self.assertTrue(os.path.isfile(cookie_path))

    def test_save_empty_rejected(self):
        success, msg, count = save_cookie_content("")
        self.assertFalse(success)
        self.assertEqual(count, 0)

        success, msg, count = save_cookie_content("just random text without netscape format")
        self.assertFalse(success)
        self.assertEqual(count, 0)

    def test_delete_cookie_files(self):
        raw_cookie = ".youtube.com\tTRUE\t/\tTRUE\t1893456000\tSID\tsample_sid\n"
        save_cookie_content(raw_cookie)
        self.assertTrue(get_cookie_status()["exists"])

        del_ok, del_msg = delete_cookie_files()
        self.assertTrue(del_ok)
        self.assertFalse(get_cookie_status()["exists"])
        self.assertIsNone(get_active_cookie_file())

    def test_is_cookie_route_requested(self):
        from unittest.mock import patch
        from frontend.cookie_route import is_cookie_route_requested

        # Negative test (standard route)
        with patch("streamlit.query_params", {}):
            self.assertFalse(is_cookie_route_requested())

        # Supported query parameters for the hidden route
        test_queries = [
            {"route": "cookies"},
            {"route": "cookie"},
            {"admin": "cookies"},
            {"admin": "cookie"},
            {"manage_cookies": "1"},
            {"manage_cookies": "true"},
            {"cookies": "1"},
            {"cookie": "true"},
            {"route": "coociee"},
        ]
        for q in test_queries:
            with patch("streamlit.query_params", q):
                self.assertTrue(is_cookie_route_requested(), f"Failed for query {q}")


if __name__ == "__main__":
    unittest.main()
