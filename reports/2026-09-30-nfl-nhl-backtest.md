# NFL/NHL-Backtest gegen Buchmacherlinien (30.09.2026)

Walk-forward: Modell wöchentlich nur mit vorher gespielten Partien neu gefittet, gleiche Parameter
wie im Scan. Markt = Eröffnungs-Moneyline (ESPN BET bzw. DraftKings, de-vigged), CLV gegen die
Closing-Line. Befehl: `python -m oddswatch backtest --us`.

| Liga | Spiele | LogLoss Modell | LogLoss Eröffnung | LogLoss Closing | bestes w | Urteil |
|---|---|---|---|---|---|---|
| NFL (Saison 2025 ab Woche 3 + 2026) | 299 | 0,648 | 0,632 | 0,625 | 0,1 (Rauschen) | nicht validiert |
| NHL (Saison 2025/26 ab 25.10.) | 1.186 | 0,697 | 0,684 | 0,683 | 0,0 | nicht validiert |

**Befund**
- In beiden Ligen ist das Modell allein schlechter als die Eröffnungslinie. Jede Beimischung zum
  Markt verschlechtert die NHL-Prognose, bei der NFL ist der Gewinn (0,63165 → 0,63157) Rauschen.
- NFL: Bei Abweichung > 5 Pp bewegt sich die Linie in 59 % der Fälle Richtung Modell
  (CLV zum fairen Eröffnungspreis +4 %, ROI ±0). Ein schwaches Signal, nur zu frühen Kursen
  nutzbar, nach Marge nicht belegbar.
- NHL: kein Signal (CLV zum fairen Preis +0,2 bis +0,7 %, ROI −0,5 bis −12 %).
- Die alte Regel (25 % Modell, Divergenzsperre 15 Pp) hätte in NHL 3 Tipps mit CLV −3,4 % erzeugt.

**Konsequenz**
- `nfl:1x2` und `nhl:1x2` stehen in `data/validation.json` als nicht validiert → Modellgewicht 0.
  Freigaben entstehen nur noch aus dem reinen Preisvergleich Kalshi gegen die DraftKings-Linie.
- Die NHL-Freigabe vom 28.09. (Hurricanes) und die NFL-Freigabe (Panthers) beruhten auf
  diesem nicht belegten Modellanteil.
