# Tennis-Runner: Bilanz aus tennis_db (Atlas, Stand 30.09.2026)

Quelle: `valuebets_history`, nur `PUBLICATION_APPROVED`, abgerechnet (won/lost). Nur lesend ausgewertet.

**Gesamt:** 335 Tipps (fast alle Aug./Sep. 2026), 135 gewonnen (40,3 %), Einsatz 204,5 EH,
Ergebnis −5,4 EH, ROI −2,6 %. Das Modell versprach im Schnitt EV +32 % (erwartet +59 EH).

| Quote | Tipps | Treffer real | Modell Ø p | Markt Ø p | Ergebnis |
|---|---|---|---|---|---|
| < 1,60 | 35 | 68,6 % | 73,3 % | 68,4 % | −0,2 EH |
| 1,60–2,19 | 84 | 50,0 % | 63,6 % | 53,0 % | −5,0 EH |
| 2,20–2,99 | 98 | 38,8 % | 51,6 % | 39,8 % | −0,8 EH |
| 3,00–4,49 | 84 | 31,0 % | 40,8 % | 27,8 % | +4,0 EH |
| ≥ 4,50 | 34 | 14,7 % | 28,6 % | 17,9 % | −3,5 EH |

- ATP 196 Tipps −1,3 EH, WTA 139 Tipps −4,1 EH; August +6,4 EH, September −10,8 EH.
- Favoriten 74 Tipps −6,3 EH, Außenseiter 261 Tipps +0,9 EH.
- CLV (99 mit Closing): Median −6,6 %, nur 18 positiv. Ohne offensichtliche Datenfehler
  (|CLV| > 30 %, meist Closing nach Spielbeginn): 66 Werte, Median −5,9 %, 6 positiv.

**Befund:** Die Trefferquote entspricht in jedem Quotenbereich dem Markt, nicht dem Modell.
Das Modell ist um rund 10–13 Pp überkalibriert, der ausgewiesene EV ist deshalb Schein.
Der negative CLV zeigt, dass die Kurse nach der Veröffentlichung gegen die Tipps laufen.
Einziger Bereich über Markt: Quote 3,00–4,49 (31,0 % vs. 27,8 %), bei 84 Tipps statistisch
nicht belastbar.

**Konsequenz:** Status INFO (nicht validiert), keine PLAY-Freigabe für Tennis. Nötig wären eine
Kalibrierung des Modells (z. B. Platt/Isotonic auf Holdout) und ein Nachweis mit positivem CLV.
