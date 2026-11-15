# btc-cent-forecast-01 — Damped Short-Horizon Momentum Ensemble

Forecast Bitcoin's price 240 minutes after each checkpoint, from the 4,320
one-minute closes (72 hours) the case gives you. Standard library only,
deterministic, offline, well inside the 8-second per-case cap.

## Method

The house baseline is persistence: guess the checkpoint's own close. That
scores a practice MAE of 44,521.58 cents (official, six cases). This entry
beats it on history by using the weak short-horizon momentum in the
one-minute closes — but a raw trend extrapolation overshoots badly, so every
trend term is damped and several windows are averaged.

The forecast is the mean of four components, all anchored on the checkpoint
close:

1. OLS slope of the last 60 closes, extrapolated 240 min, damped ×0.20
2. OLS slope of the last 75 closes, extrapolated 240 min, damped ×0.25
3. OLS slope of the last 45 closes, extrapolated 240 min, damped ×0.15
4. Median 1-minute return of the last 60 closes × 240 min, damped ×0.30
   (robust to the pool's one-minute jumps; when the median minute does not
   move, this component is exactly persistence)

The guess is clamped to the scorer's (0, 10,000,000) range and rounded to
the price grid's 5 decimals.

## Practice validation

Practice cases sit 4 hours apart, so each case's target is the next case's
checkpoint close (p00–p04; p05's target is not in the kit):

| method | MAE (cents) |
|---|---|
| persistence (house baseline) | 47,055 |
| this ensemble | 36,555 |

About 22% below persistence on the five measurable practice cases, and the
leave-one-out MAE stays between 25,962 and 42,767 cents, so the edge is not
one lucky case. The final is scored on unseen prices, so no practice number
guarantees the final — it only shows the method beats persistence on
history instead of merely assuming it does.

## Run

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `*.in` in the input directory and writes one `<id>.out` per
case: `{"forecasts": [{"case": "<id>", "price": <number>}]}`. Two runs on
the same case write byte-identical output.

## License

MIT — see `LICENSE`.
