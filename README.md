# oddswatch

Selbstständiger Scan, unabhängige Bewertung und Preisvergleich für Fußball
(Bundesliga, 2. Bundesliga, österreichische Bundesliga, UEFA), NFL, NHL und NBA,
mit getrennten Ledgern, CLV-Nachkontrolle und deutschen CEO- und Telegram-Texten.

## Befehle

```bash
python -m oddswatch scan                 # Scan (7 Tage Freigabe, 14 Tage Watchlist) + Journal + Bericht
python -m oddswatch scan --dry           # nur Bericht, nichts ins Journal
python -m oddswatch scan --send          # zusätzlich Telegram-Versand (Bot API)
python -m oddswatch settle               # Kalshi-Ergebnisse abrufen, abrechnen, CLV
python -m oddswatch place --ref KXNFLGAME-26OCT04DETCAR-CAR --odds 2.66 --stake 0.75
python -m oddswatch send reports/<datum>-telegram.txt
python -m oddswatch summary
python -m pytest -q
```

## Ablauf

1. **Daten**: football-data.co.uk (Ergebnisse, echte xG ab 2026/27, bet365-Closing
   für AT), ESPN (Spielpläne, Ergebnisse, NFL-Verletzungen, DraftKings-Referenzlinie),
   NHL-API (Ergebnisse, 5v5-Tore, PP/PK), Kalshi-API (Preise, Orderbuch-Tiefe, Ergebnisse).
2. **Modelle**: Fußball und Eishockey mit Poisson (Dixon-Coles, Zeitverfall, im Fußball
   Tore und xG je 50 %), NFL mit Punkte-Rating (Offense/Defense, Heimvorteil, σ aus Residuen).
3. **Fair**: `p_final = w·p_model + (1−w)·p_ref`. Die Referenz ist die de-vigged
   DraftKings-Linie, ersatzweise der Kalshi-Mittelkurs. `w` ist die angenommene
   Modellzuverlässigkeit (Fußball 0,5, NFL 0,25, NHL 0,25).
4. **Preis**: Kalshi-Ask inkl. Taker-Gebühr (Order ≈ 100 Kontrakte).
   Orbit und bet365 sind hier nicht abrufbar und werden nie ungeprüft verwendet.
5. **Freigabe**: höchstens 5 Kandidaten, je Event einer. Bedingungen:
   - EV ≥ 3 % und Edge ≥ 2 Pp
   - kein Newsvorbehalt (z. B. QB fehlt), keine Modell-Markt-Divergenz > 15 Pp
   - Anstoß im Freigabefenster

   Einsatz: ¼-Kelly mit Schätzungsabschlag, maximal 2 EH.
6. **Journal** (`data/journal/`): `forecasts.csv` (alle Prognosen),
   `valuebets.csv` (freigegebene Tipps), `placed.csv` (tatsächlich gespielt).
   Kalshi-Snapshots (`data/snapshots/`) liefern die Closing Line für den CLV.

## Telegram ohne Make

Die Umgebungsvariablen `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` setzen, dann
`python -m oddswatch scan --send` oder `python -m oddswatch send <datei>`.
Als gesendet gilt eine Nachricht nur, wenn Telegram `ok=true` und eine `message_id` liefert.
