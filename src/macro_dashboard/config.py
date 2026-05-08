"""Central configuration for Macro Argentina Dashboard.

All API URLs, series IDs, cache settings, and thresholds live here.
No magic strings or numbers should appear in other modules.
"""

from pathlib import Path

# ── Project paths ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_CACHE_DIR = PROJECT_ROOT / "data" / "cache"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

# Ensure directories exist at import time
DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── BCRA API ──────────────────────────────────────────────────────────────────
BCRA_BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0"
BCRA_TIMEOUT_SECONDS = 10
BCRA_MAX_RETRIES = 3
BCRA_BACKOFF_SECONDS = 2.0

# BCRA series IDs (integer IdVariable) — verify against https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias
# before first run. These IDs have changed historically between API versions.
BCRA_SERIES: dict[str, int] = {
    "tc_oficial_minorista": 4,  # Tipo de cambio minorista ($ por USD)
    "tc_mayorista": 5,  # Tipo de cambio mayorista
    "reservas_brutas": 1,  # Reservas internacionales brutas (USD mn)
    "tasa_politica_monetaria": 161,  # Tasa de política monetaria (% TNA)
    "badlar_privados": 7,  # Tasa BADLAR bancos privados (% TNA)
    "base_monetaria": 15,  # Base monetaria (millones de $)
}

BCRA_SERIES_START_DATE = "2017-01-01"  # IPC base confiable desde aquí

# ── INDEC / datos.gob.ar API ──────────────────────────────────────────────────
INDEC_BASE_URL = "https://apis.datos.gob.ar/series/api"
INDEC_TIMEOUT_SECONDS = 15
INDEC_MAX_RETRIES = 2

# Series IDs from datos.gob.ar — buscar en https://datos.gob.ar/series
INDEC_SERIES = {
    "ipc_total": "148.3_INIVELNAL_DICI16_M_26",  # IPC Nacional mensual
    "ipc_nucleo": "148.3_INUCLEONAL_DICI16_M_14",  # IPC Núcleo mensual
    "ipc_regulados": "148.3_IREGULNAL_DICI16_M_29",  # IPC Regulados mensual
    "ipc_estacionales": "148.3_IESTACNAL_DICI16_M_32",  # IPC Estacionales
    "ipc_alimentos": "148.3_IALIMBEBI_DICI16_M_13",  # IPC Alimentos y Bebidas
    "emae": "143.3_NO_PR_2004_A_21",  # EMAE mensual
}

INDEC_START_DATE = "2017-01-01"  # Base IPC dic-2016 = 100

# ── Cache settings ─────────────────────────────────────────────────────────────
# TTL en segundos para st.cache_data de Streamlit
CACHE_TTL_BCRA_SECONDS = 3600  # BCRA actualiza diariamente: 1h suficiente
CACHE_TTL_INDEC_SECONDS = 3600 * 6  # INDEC actualiza mensualmente: 6h suficiente

# ── Thresholds for dashboard indicators ───────────────────────────────────────
# Umbrales del semáforo de inflación mensual (referenciados a targets históricos BCRA)
INFLACION_UMBRAL_ROJO = 0.05  # > 5% mensual → rojo
INFLACION_UMBRAL_AMARILLO = 0.03  # 3-5% mensual → amarillo
# < 3% mensual → verde

# Umbral tasa real negativa (BADLAR - inflación)
TASA_REAL_UMBRAL_ALERTA = -0.05  # < -5% mensual → alerta

# Número de meses default para gráficos
DEFAULT_MONTHS_WINDOW = 36
