"""Unit tests for HTTP data clients.

All tests are fully isolated — no real HTTP calls are made. External
dependencies are replaced with unittest.mock objects.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock

from macro_dashboard.data.clients.bcra_client import BCRAClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_mock_response(detalle: list) -> MagicMock:
    """Build a mock requests.Response that returns a v4-shaped JSON payload.

    The BCRA v4 API wraps time-series data under results[0]['detalle'].

    Args:
        detalle: List of {'fecha': str, 'valor': float} dicts to embed.

    Returns:
        MagicMock configured to behave like a successful HTTP response.
    """
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()  # no-op: simulates HTTP 200
    mock_resp.json.return_value = {
        "status": 200,
        "metadata": {"resultset": {"count": len(detalle), "offset": 0, "limit": len(detalle)}},
        "results": [
            {
                "idVariable": 4,
                "detalle": detalle,
            }
        ],
    }
    return mock_resp


# ── BCRAClient tests ───────────────────────────────────────────────────────────

class TestBCRAClient:
    """Tests for BCRAClient — BCRA Estadísticas v4.0 HTTP client."""

    def test_bcra_fetch_series_returns_correct_columns(self):
        """DataFrame returned by fetch_series must have ['fecha', 'valor'] with
        the correct dtypes: datetime64[ns] and float64 respectively."""
        detalle = [
            {"fecha": "2024-01-31", "valor": 827.5},
            {"fecha": "2024-02-29", "valor": 834.2},
        ]
        mock_resp = _make_mock_response(detalle)

        with patch("requests.Session.get", return_value=mock_resp):
            client = BCRAClient()
            df = client.fetch_series("tc_oficial_minorista")

        assert list(df.columns) == ["fecha", "valor"]
        assert str(df["fecha"].dtype) == "datetime64[ns]"
        assert str(df["valor"].dtype) == "float64"
        assert len(df) == 2

    def test_bcra_fetch_series_unknown_key_raises_keyerror(self):
        """fetch_series must raise KeyError before any HTTP call is made when
        the serie_key is not present in config.BCRA_SERIES."""
        client = BCRAClient()
        with pytest.raises(KeyError, match="clave_inexistente"):
            client.fetch_series("clave_inexistente")

    def test_bcra_retry_on_connection_error(self):
        """On repeated ConnectionError the retry decorator must exhaust all
        attempts and then raise RuntimeError with 'unavailable after' in the
        message."""
        with patch(
            "requests.Session.get",
            side_effect=requests.ConnectionError("simulated timeout"),
        ):
            client = BCRAClient()
            with pytest.raises(RuntimeError, match="unavailable after"):
                client.fetch_series("tc_oficial_minorista")

    def test_bcra_empty_results_returns_empty_dataframe(self):
        """When the API returns results: [] the client must return an empty
        DataFrame with ['fecha', 'valor'] columns — no exception raised."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "status": 200,
            "metadata": {"resultset": {"count": 0, "offset": 0, "limit": 0}},
            "results": [],
        }

        with patch("requests.Session.get", return_value=mock_resp):
            client = BCRAClient()
            df = client.fetch_series("tc_oficial_minorista")

        assert list(df.columns) == ["fecha", "valor"]
        assert len(df) == 0

    def test_bcra_empty_detalle_returns_empty_dataframe(self):
        """When results[0]['detalle'] is empty the client must return an empty
        DataFrame with ['fecha', 'valor'] columns — no exception raised."""
        mock_resp = _make_mock_response(detalle=[])

        with patch("requests.Session.get", return_value=mock_resp):
            client = BCRAClient()
            df = client.fetch_series("tc_oficial_minorista")

        assert list(df.columns) == ["fecha", "valor"]
        assert len(df) == 0

    def test_bcra_fetch_series_sorted_ascending(self):
        """Rows must be sorted in ascending chronological order, regardless of
        the order returned by the API."""
        detalle = [
            {"fecha": "2024-03-31", "valor": 850.0},
            {"fecha": "2024-01-31", "valor": 827.5},
            {"fecha": "2024-02-29", "valor": 834.2},
        ]
        mock_resp = _make_mock_response(detalle)

        with patch("requests.Session.get", return_value=mock_resp):
            client = BCRAClient()
            df = client.fetch_series("tc_oficial_minorista")

        assert df["fecha"].is_monotonic_increasing

    def test_bcra_fetch_series_drops_duplicate_dates(self):
        """Duplicate dates in the API response must be deduplicated, keeping
        the first occurrence after sorting."""
        detalle = [
            {"fecha": "2024-01-31", "valor": 827.5},
            {"fecha": "2024-01-31", "valor": 999.9},  # duplicate
            {"fecha": "2024-02-29", "valor": 834.2},
        ]
        mock_resp = _make_mock_response(detalle)

        with patch("requests.Session.get", return_value=mock_resp):
            client = BCRAClient()
            df = client.fetch_series("tc_oficial_minorista")

        assert len(df) == 2
        assert df["fecha"].nunique() == len(df)
