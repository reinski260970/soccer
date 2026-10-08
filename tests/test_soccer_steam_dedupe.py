from oddswatch import quick


def _sig(direction="SHORTENING", p=0.52):
    return {
        "key": "soccer:1:home",
        "direction": direction,
        "lead_source": "Pinnacle",
        "probs": {"Pinnacle": p, "Bet365": 0.50},
    }


def test_soccer_dedupe_same_signal_not_repeated():
    state = {}
    first = quick._fresh_signals([_sig()], state)
    assert len(first) == 1
    quick._mark_sent(first, state)

    assert quick._fresh_signals([_sig()], state) == []


def test_soccer_dedupe_requires_extension_or_direction_flip():
    state = {}
    first = [_sig(p=0.52)]
    quick._mark_sent(first, state)

    assert quick._fresh_signals([_sig(p=0.534)], state) == []
    assert len(quick._fresh_signals([_sig(p=0.536)], state)) == 1
    assert len(quick._fresh_signals([_sig(direction="DRIFTING", p=0.52)], state)) == 1
