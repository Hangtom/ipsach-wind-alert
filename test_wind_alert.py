import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import wind_alert


SAMPLE = '<div>Wind-10min-Max: 37.0km/h (20.0kn, 5Bf) O</div>'


class WindAlertTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / "state.json"
        self.state.write_text('{"alert_active": false}\n')

    def test_parses_knots(self):
        self.assertEqual(wind_alert.parse_wind_knots(SAMPLE), 20.0)

    @patch("wind_alert.send_notification")
    @patch("wind_alert.fetch_text", return_value=SAMPLE)
    def test_alerts_once_and_does_not_spam(self, _fetch, notify):
        now = datetime(2026, 8, 12, 12, tzinfo=ZoneInfo("Europe/Zurich"))
        with patch.object(wind_alert, "STATE_FILE", self.state), patch.dict(
            "os.environ", {"NTFY_TOPIC": "test-topic"}
        ):
            wind_alert.run(now)
            wind_alert.run(now)
        self.assertEqual(notify.call_count, 1)

    @patch("wind_alert.send_notification")
    @patch("wind_alert.fetch_text", return_value=SAMPLE)
    def test_no_alert_outside_daytime(self, _fetch, notify):
        now = datetime(2026, 8, 12, 20, tzinfo=ZoneInfo("Europe/Zurich"))
        with patch.object(wind_alert, "STATE_FILE", self.state):
            wind_alert.run(now)
        notify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
