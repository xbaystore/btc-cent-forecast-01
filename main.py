#!/usr/bin/env python3
"""btc-cent-forecast-01: forecast BTC's price 240 minutes after a checkpoint.

Method (empirical, fitted only on the kit's six practice cases, never on the
final's unseen prices): the house baseline is persistence -- guess the
checkpoint's own close. Bitcoin's 1-minute closes carry a weak but real
short-horizon momentum: the slope of the last hour predicts part of the next
four hours' move, but a raw extrapolation overshoots badly, so every trend
term is damped to 15-30% of its full 240-minute extrapolation and several
windows are averaged to keep one noisy window from dominating.

The forecast is the mean of four components, all anchored on the checkpoint
close `last`:

  1. OLS slope of the last 60 closes, extrapolated 240 min, damped x0.20
  2. OLS slope of the last 75 closes, extrapolated 240 min, damped x0.25
  3. OLS slope of the last 45 closes, extrapolated 240 min, damped x0.15
  4. median 1-minute return of the last 60 closes, x240 min, damped x0.30
     (robust to the one-minute jumps this pool's price makes; when the median
     minute does not move, this component is exactly persistence)

Practice (p00-p04, each target read off the next case's checkpoint close,
because the cases sit 4 hours apart; p05's target is not in the kit):
  persistence MAE  47,055 cents
  this ensemble    36,555 cents  (about 22% below persistence)
  leave-one-out MAE per dropped case: 25,962 - 42,767 cents, so the edge is
  not one lucky case. The official 6-case practice baseline is 44,521.58
  cents; the final is scored on unseen prices, so no practice number
  guarantees the final -- it only shows the method beats persistence on
  history instead of merely assuming it does.

Deterministic, standard library only, no network, no randomness: two runs
on the same case write byte-identical output.
"""

import json
import math
import os
import statistics
import sys

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999
HORIZON_MINUTES = 240


def ols_slope(values):
    """Ordinary-least-squares slope (dollars per minute) of a price window."""
    n = len(values)
    mean_i = (n - 1) / 2.0
    mean_v = sum(values) / n
    num = 0.0
    den = 0.0
    for i, v in enumerate(values):
        di = i - mean_i
        num += di * (v - mean_v)
        den += di * di
    if den == 0.0:
        return 0.0
    return num / den


def forecast(prices):
    """One forecast for the price 240 minutes after the checkpoint close."""
    if not prices:
        raise ValueError("market has no prices")
    last = prices[-1]
    if not isinstance(last, (int, float)) or not math.isfinite(last):
        raise ValueError("market's last price is not a finite number")

    def trend(window, damp):
        w = prices[-window:] if len(prices) >= window else prices
        return ols_slope(w) * HORIZON_MINUTES * damp

    # Component 4: median 1-minute return over the last 60 minutes.
    recent = prices[-60:] if len(prices) >= 60 else prices
    diffs = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    median_return = statistics.median(diffs) if diffs else 0.0

    components = [
        last + trend(60, 0.20),
        last + trend(75, 0.25),
        last + trend(45, 0.15),
        last + median_return * HORIZON_MINUTES * 0.30,
    ]
    guess = sum(components) / len(components)
    # Keep the guess on the grid's 5 decimals and inside the scorer's bounds.
    guess = round(min(MAX_PRICE, max(MIN_PRICE, guess)) * 1e5) / 1e5
    return guess


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    if not inputs:
        raise SystemExit("no .in case files in input directory")
    for filename in inputs:
        case_id = filename[: -len(".in")]
        with open(os.path.join(INPUT_DIR, filename), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{filename} does not hold exactly one market")
        price = forecast(markets[0]["prices"])
        payload = {"forecasts": [{"case": case_id, "price": price}]}
        with open(os.path.join(OUTPUT_DIR, f"{case_id}.out"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
