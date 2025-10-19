import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services import (
    forecast_linear_band,
    forecast_holt_linear,
    band_from_moving_stats,
    detect_linear_anomalies,
    detect_ts_anomalies,
)

def test_forecast_linear_band_basic():
    s = pd.Series([1, 2, 3, 4, 5, 6])
    f, lo, hi = forecast_linear_band(s, window=6, horizon=3, k=2.0)
    assert len(f) == 3
    assert np.allclose(f, [7, 8, 9])
    assert np.allclose(lo, hi)

def test_forecast_holt_linear_trend():
    s = pd.Series([1, 2, 3, 4])
    f = forecast_holt_linear(s, alpha=1.0, beta=1.0, horizon=2)
    assert np.allclose(f, [5, 6])

def test_band_from_moving_stats_mean():
    s = pd.Series([1, 2, 3, 4, 5, 6])
    f, lo, hi = band_from_moving_stats(s, window=3, horizon=2, k=1.0)
    assert np.allclose(f, [5, 5])
    assert lo[0] < f[0] < hi[0]

def test_detect_linear_anomalies():
    s = pd.Series([1, 1, 1, 1, 10, 1, 1])
    res = detect_linear_anomalies(s, window=3, threshold=2.5, robust=False)
    assert not res.empty
    assert 4 in res["month"].values


def test_detect_ts_anomalies_stl():
    months = pd.period_range("2020-01", periods=24, freq="M").strftime("%Y-%m")
    data = np.ones(len(months)) * 50
    data[10] = 120
    data[15] = 60
    series = pd.Series(data, index=months)
    res = detect_ts_anomalies(series, method="stl", threshold=2.5, seasonal_periods=12)
    assert not res.empty
    assert any(m in res["month"].values for m in [months[10], months[11], months[15]])


def test_detect_ts_anomalies_arima():
    months = pd.period_range("2021-01", periods=20, freq="M").strftime("%Y-%m")
    data = np.linspace(10, 30, len(months))
    data[15] += 20
    series = pd.Series(data, index=months)
    res = detect_ts_anomalies(series, method="arima", threshold=2.0)
    assert not res.empty
    assert any(m in res["month"].values for m in [months[15], months[14]])
