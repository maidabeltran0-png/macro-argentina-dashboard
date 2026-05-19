# Macro Argentina Dashboard

> Real-time macroeconomic monitoring system: inflation, exchange rate, interest rates, and BCRA reserves — featuring derived metrics and historical time series.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

## Demo

![Dashboard Demo](https://via.placeholder.com/800x400.png?text=Dashboard+Demo+GIF+Coming+Soon)
*(Note: Please add a GIF or screenshot of the working dashboard here)*

## Monitored Variables

- **Inflation:** Disaggregated monthly CPI (core, regulated, seasonal) + 12M accumulated.
- **Exchange Rate:** Official FX + monthly variation + bilateral real FX (approx.).
- **Rates:** Nominal BADLAR + ex-post real rate + spread vs. monetary policy rate (TPM).
- **Reserves:** Gross reserves + net reserves approximation + weeks of imports.

## Stack

Python · Streamlit · Plotly · pandas · requests · statsmodels

## Data Sources

- BCRA API Estadísticas Cambiarias v4
- INDEC / datos.gob.ar Time Series

## Technical Highlight: BCRA API Integration

This project features a robust, testable HTTP client specifically designed to interact with the **BCRA Estadísticas Cambiarias API v4**, which provides superior time-series consistency for accurate macroeconomic tracking. 

Key technical aspects include:
- **Resilience**: Decorator-based retry mechanism with exponential backoff ensures uninterrupted data flow despite network instabilities or rate limits.
- **Data Normalization**: Seamless conversion of raw API JSON responses into fully typed `pandas` DataFrames.
- **Reliability**: Comprehensive test suite utilizing `pytest` and `unittest.mock` to validate error handling and connectivity resilience.

## Upcoming Tasks & Roadmap

- [ ] Develop and style the Streamlit dashboard user interface.
- [ ] Add project demonstration GIF to README.
- [ ] Deploy dashboard to Streamlit Cloud.
