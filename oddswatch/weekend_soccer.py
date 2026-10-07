"""Weekend soccer scan across every league supported by the live data stack.

This is a SHADOW scan while soccer production release is frozen.
Model fair probabilities remain independent from market prices.
Entry layer:
  model fair -> current executable odds -> Pinnacle no-vig -> steam direction.

No SHADOW candidate is written as an official PLAY/Sharpery bet.
Predictions are still persisted to SQL/Neon for forward evaluation.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import report, scan, telegram
from .journal import Journal

TZ = ZoneInfo("Europe/Vienna")
MIN_MODEL_EV = 0.03
MIN_CLV_CASE = 0.01
MAX_ROWS = 18


def next_weekend(today: date | None = None) -> tuple[date, date]:
    today = today or datetime.now(TZ).date()
    # Friday=4. If today is Fri/Sat/Sun, use the current weekend.
    wd = today.weekday()
    if wd <= 4:
        friday = today + timedelta(days=(4 - wd))
    elif wd == 5:
        friday = today - timedelta(days=1)
    else:
        friday = today - timedelta(days=2)
    return friday, friday + timedelta(days=2)


def _model_ev(c) -> float:
    return float(c.p_model) * float(c.odds) - 1.0


def _model_edge(c) -> float:
    return float(c.p_model) - 1.0 / float(c.odds)


def _steam_text(row: dict | None) -> str:
    if not row:
        return "NO_STEAM_DATA"
    sig = row.get("signal")
    if not sig:
        gap = float(row.get("gap") or 0.0)
        if gap >= 0.008:
            return f"SHARP_GAP+ {gap*100:+.1f}pp"
        if gap <= -0.008:
            return f"SHARP_GAP- {gap*100:+.1f}pp"
        return "NEUTRAL"
    if sig.get("direction") == "SHORTENING":
        return (
            f"STEAM+ Pin {float(sig.get('lead_move') or 0)*100:+.1f}pp/"
            f"{int(sig.get('minutes') or 0)}m"
        )
    return (
        f"STEAM- Pin {float(sig.get('lead_move') or 0)*100:+.1f}pp/"
        f"{int(sig.get('minutes') or 0)}m"
    )


def _status(c, row: dict | None) -> str:
    model_ev = _model_ev(c)
    clv = float((row or {}).get("clv_to_sharp") or 0.0)
    sig = (row or {}).get("signal")
    if sig and sig.get("direction") == "DRIFTING":
        return "PASS"
    if model_ev >= MIN_MODEL_EV and clv >= MIN_CLV_CASE:
        return "SHADOW-PLAY"
    if model_ev > 0 and clv > 0:
        return "WATCH"
    return "PASS"


def _best_candidates(res) -> list[tuple]:
    best = {}
    for c in res.candidates:
        if c.league in {"nfl", "nhl", "nba", "del", "icehl", "liiga", "shl", "nl", "khl"}:
            continue
        key = (c.event, c.market)
        if key not in best or float(c.odds) > float(best[key].odds):
            best[key] = c

    rows = []
    state = getattr(res, "steam_state", {}) or {}
    for key, c in best.items():
        s = state.get(key)
        status = _status(c, s)
        if status == "PASS":
            continue
        model_ev = _model_ev(c)
        clv = float((s or {}).get("clv_to_sharp") or 0.0)
        score = model_ev + max(clv, 0.0)
        rows.append((status, score, c, s, model_ev, _model_edge(c), clv))
    rows.sort(key=lambda x: (x[0] != "SHADOW-PLAY", -x[1]))
    return rows


def build(*, today: date | None = None) -> tuple[str, object]:
    friday, sunday = next_weekend(today)
    j = Journal()
    res = scan.run(
        start=friday,
        days=2,
        watch_days=2,
        sports=("soccer",),
        journal=j,
    )

    coverage = defaultdict(lambda: {"games": 0, "priced": 0, "refs": 0, "models": set()})
    for fx in res.fixtures:
        if not (friday <= fx.game.kickoff.astimezone(TZ).date() <= sunday):
            continue
        r = coverage[fx.league]
        r["games"] += 1
        r["priced"] += int(bool(fx.offers))
        r["refs"] += int(bool(fx.ref_probs))
        r["models"].add(fx.model or "soccer")

    rows = _best_candidates(res)
    lines = [
        f"⚽ WOCHENEND-SCAN · {friday:%d.%m.}–{sunday:%d.%m.%Y}",
        "Alle im Live-Stack unterstützten Fußballligen · SHADOW bis Soccer-Release",
        "",
        "📚 ABDECKUNG",
    ]
    if not coverage:
        lines.append("Keine bewertbaren Wochenendspiele gefunden.")
    else:
        for league, r in sorted(coverage.items(), key=lambda x: report._league(x[0])):
            models = ",".join(sorted(r["models"]))
            lines.append(
                f"• {report._league(league)}: {r['games']} Spiele · "
                f"Preise {r['priced']}/{r['games']} · Ref {r['refs']}/{r['games']} · {models}"
            )

    plays = [x for x in rows if x[0] == "SHADOW-PLAY"]
    watches = [x for x in rows if x[0] == "WATCH"]
    lines += ["", f"🟢 SHADOW-PLAY-KANDIDATEN ({len(plays)})"]
    if not plays:
        lines.append("Keine Kandidaten erfüllen aktuell Fair + Markt + CLV-Gate.")
    for _, _, c, s, mev, medge, clv in plays[:MAX_ROWS]:
        sharp = (s or {}).get("sharp_fair")
        model_fair = 1.0 / float(c.p_model)
        lines += [
            f"• {report._league(c.league)} · {report._kick(c.kickoff)}",
            f"  {c.event} · {c.selection}",
            f"  Modell fair {model_fair:.2f} · Markt {float(c.odds):.2f} ({c.source}) · "
            + (f"Pinnacle no-vig {float(sharp):.2f}" if sharp else "Pinnacle no-vig –"),
            f"  Modell-EV {mev*100:+.1f}% · Edge {medge*100:+.1f}pp · "
            f"CLV-Case {clv*100:+.1f}% · {_steam_text(s)}",
            f"  Modell: {c.reason.split(' – ')[0] if c.reason else 'live'}",
        ]

    lines += ["", f"🟡 WATCH ({len(watches)})"]
    for _, _, c, s, mev, medge, clv in watches[:10]:
        lines.append(
            f"• {report._league(c.league)} · {c.event} · {c.selection} @ {float(c.odds):.2f} "
            f"| Fair {1/float(c.p_model):.2f} | Modell-EV {mev*100:+.1f}% "
            f"| CLV-Case {clv*100:+.1f}% | {_steam_text(s)}"
        )

    lines += [
        "",
        "REGEL: Marktpreise/Steam sind Entry-Layer, keine Modellfeatures.",
        "Bestätigter STEAM− = PASS. SHADOW-PLAY zählt nicht als Sharpery/echter PLAY.",
        "M17.11 ist noch nicht ligaweit im Live-Scoring aktiv; Modellname wird je Liga ausgewiesen.",
    ]
    return "\n".join(lines) + "\n", res


def run(*, send: bool = False, today: date | None = None) -> int:
    text, _ = build(today=today)
    print(text)
    if not send:
        return 0
    result = telegram.send(text)
    if not result["sent"]:
        print(f"Telegram: NICHT gesendet – {result['error']}")
        return 2
    print(f"Telegram: gesendet, message_id {result['message_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(send=True))
