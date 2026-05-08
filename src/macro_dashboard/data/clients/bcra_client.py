"""HTTP client for the BCRA Estadísticas v4.0 API.

Handles retries, backoff, and response parsing. Returns normalized DataFrames.
No business logic lives here — only HTTP and parsing.

API contract: https://api.bcra.gob.ar/estadisticas/v4.0/
Data endpoint: GET /estadisticas/v4.0/Monetarias/{IdVariable}
Response shape:
    {
        "status": 200,
        "metadata": {"resultset": {"count": N, "offset": 0, "limit": N}},
        "results": [
            {
                "idVariable": <int>,
                "detalle": [
                    {"fecha": "YYYY-MM-DD", "valor": <float>},
                    ...
                ]
            }
        ]
    }
"""

import logging
import time
from functools import wraps
from typing import Callable, Any

import pandas as pd
import requests

from macro_dashboard.config import (
    BCRA_BASE_URL,
    BCRA_TIMEOUT_SECONDS,
    BCRA_MAX_RETRIES,
    BCRA_BACKOFF_SECONDS,
    BCRA_SERIES,
    BCRA_SERIES_START_DATE,
)

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int, backoff_seconds: float) -> Callable:
    """Decorator: retries the wrapped function on network/timeout errors.

    Uses exponential backoff to avoid hammering an already-overloaded API.

    Args:
        max_retries: Maximum number of attempts before raising RuntimeError.
        backoff_seconds: Base wait time; actual wait = backoff_seconds ** attempt.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                    wait = backoff_seconds ** attempt
                    logger.warning(
                        "BCRA API call failed (attempt %d/%d): %s. Retrying in %.1fs",
                        attempt + 1, max_retries, exc, wait,
                    )
                    time.sleep(wait)
            raise RuntimeError(
                f"BCRA API unavailable after {max_retries} retries. "
                "Check https://api.bcra.gob.ar/estadisticas/v4.0/ manually."
            )
        return wrapper
    return decorator


class BCRAClient:
    """Client for the BCRA Estadísticas v4.0 API (Monetarias endpoint).

    Fetches time-series data by integer IdVariable and normalizes the response
    into a pandas DataFrame with columns ['fecha', 'valor'] and dtypes
    [datetime64[ns], float64].

    The v4 API nests the time-series array under results[0]['detalle'], unlike
    the flat 'results' list used in v3.
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    @retry_on_failure(
        max_retries=BCRA_MAX_RETRIES,
        backoff_seconds=BCRA_BACKOFF_SECONDS,
    )
    def fetch_series(
        self,
        serie_key: str,
        desde: str = BCRA_SERIES_START_DATE,
    ) -> pd.DataFrame:
        """Fetch a BCRA statistical series and return it as a normalized DataFrame.

        Calls GET /estadisticas/v4.0/Monetarias/{IdVariable}?Desde=<date>.

        Args:
            serie_key: Key from config.BCRA_SERIES (e.g., 'tc_oficial_minorista').
            desde: Start date in 'YYYY-MM-DD' format.

        Returns:
            DataFrame with columns ['fecha' (datetime64[ns]), 'valor' (float64)],
            sorted ascending by date, with no duplicate dates.

        Raises:
            KeyError: If serie_key is not in config.BCRA_SERIES.
            RuntimeError: If the API is unreachable after max_retries.
        """
        if serie_key not in BCRA_SERIES:
            raise KeyError(
                f"Unknown series key: '{serie_key}'. "
                f"Valid keys: {list(BCRA_SERIES.keys())}"
            )

        id_variable: int = BCRA_SERIES[serie_key]
        url = f"{BCRA_BASE_URL}/Monetarias/{id_variable}"
        # v4 uses 'Desde' (capitalized) as query param with date-time format
        params = {"Desde": desde}

        logger.info(
            "Fetching BCRA series '%s' (IdVariable=%d) from %s",
            serie_key, id_variable, desde,
        )

        response = self._session.get(url, params=params, timeout=BCRA_TIMEOUT_SECONDS)
        response.raise_for_status()

        return self._parse_response(response.json(), serie_key)

    def _parse_response(self, raw: dict, serie_key: str) -> pd.DataFrame:
        """Parse raw BCRA v4 JSON response into a normalized DataFrame.

        The v4 API wraps the time-series under results[0]['detalle']. If the
        results list is empty or detalle is missing/empty, an empty DataFrame
        with the correct columns is returned instead of raising an exception.

        Args:
            raw: Raw JSON dict from the BCRA v4 API.
            serie_key: Series key used for logging context.

        Returns:
            Normalized DataFrame with ['fecha' (datetime64[ns]), 'valor' (float64)]
            columns, sorted ascending by date, with duplicate dates removed.
        """
        results: list = raw.get("results", [])
        if not results:
            logger.warning("BCRA returned empty results for series '%s'", serie_key)
            return pd.DataFrame(columns=["fecha", "valor"])

        # v4 nests the time-series array inside results[0]['detalle']
        detalle: list = results[0].get("detalle", [])
        if not detalle:
            logger.warning(
                "BCRA results[0]['detalle'] is empty for series '%s'", serie_key
            )
            return pd.DataFrame(columns=["fecha", "valor"])

        # v4 already uses 'fecha' and 'valor' as keys — no rename needed
        df = pd.DataFrame(detalle)
        df["fecha"] = pd.to_datetime(df["fecha"]).astype("datetime64[ns]")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = (
            df[["fecha", "valor"]]
            .sort_values("fecha")
            .drop_duplicates(subset="fecha")
            .reset_index(drop=True)
        )

        logger.info(
            "BCRA series '%s': %d rows, from %s to %s",
            serie_key, len(df),
            df["fecha"].min().date(),
            df["fecha"].max().date(),
        )
        return df
