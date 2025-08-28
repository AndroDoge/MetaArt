# Seeking / Self-Seeking Streams (MVP Spec)

Idea: Stream (noise generator) ei jää passiivisesti yksin jos kukaan ei kuuntele, vaan siirtyy “seeking”-tilaan, julkaisee beacon-viestejä ja etsi listeneriä. Listener-simulaatioprosessi poimii beaconin ja “subscribeaa” streamiin. Tämä on _supply-driven discovery_.

## Terminologia
| Termi | Kuvaus |
|-------|--------|
| Stream | Yksittäinen noise prosessi (esim. noise_metadata) |
| Listener | Simuloitu tai oikea kuluttaja joka haluaa dataa |
| Loneliness (orphan score) | Kuinka monta tuotettua tickiä ei ole (vielä) toimitettu kuluttajille |
| Beacon | Yksi JSON-objekti (rivi) joka kuvaa streamin profiilia & etsintätilaa |
| Subscription | Listenerin ilmoitus että se ottaa streamin vastaan |
| State Machine | idle -> seeking_low -> seeking_escalate -> attached -> (commons | shutdown) |

## MVP Scope
- Ei verkko- / Redis-riippuvuutta.
- Käytetään paikallista hakemistoa `runtime/`.
- Beaconit kirjoitetaan tiedostoon `runtime/beacons.jsonl` (yksi JSON per rivi).
- Subscriptionit ylläpidetään tiedostossa `runtime/subscriptions.json`.
- Listener-simulaatio `scripts/listener_sim.py` pollaa beacon-tiedostoa, valitsee tuoreimman, ja lisää listener-id:n subscriptioneihin.
- Stream core seuraa tuotettujen tickien määrää ja delivered-countia (aluksi delivered stubataan = 0 kunnes oikea kulutuspolku toteutuu). Kun raja ylittyy, se generoi beaconin.

## Ympäristömuuttujat (Seeking)
| Env | Oletus | Kuvaus |
|-----|--------|--------|
| NOISE_SEEK_LONELY_AFTER_S | 12 | Sekunteja ilman listeneriä ennen kuin siirrytään seeking_low |
| NOISE_SEEK_ESCALATE_AFTER_S | 30 | Sekunteja ilman listeneriä -> seeking_escalate (aggressiivisempi beacon-tahti) |
| NOISE_SEEK_SHUTDOWN_AFTER_S | 120 | Sekunteja ilman listeneriä -> harkitse shutdown tai commons merge (MVP: loggaa intent) |
| NOISE_SEEK_BEACON_PATH | runtime/beacons.jsonl | Beacon JSONL polku |
| NOISE_SEEK_SUBSCRIPTIONS_PATH | runtime/subscriptions.json | Subscription map polku |
| NOISE_SEEK_BEACON_INTERVAL_LOW_S | 10 | Minimi väli beaconille seeking_low tilassa |
| NOISE_SEEK_BEACON_INTERVAL_ESC_S | 5 | Minimi väli beaconille seeking_escalate tilassa |

## Beacon Formaatti (JSONL rivi)
```
{
  "ts": "2025-08-28T21:00:12.345Z",
  "stream_id": "noise_metadata",
  "state": "seeking_low",
  "seq": 182,
  "produced_ticks": 182,
  "delivered_ticks": 0,
  "loneliness_ratio": 1.0,
  "mode": "markov",
  "entropy_profile": "unknown",          // stub, voidaan laskea entropiaikkunan perusteella
  "tempo_range_s": [1.0, 4.0],
  "tokens_hint": ["aurora","mesh","lumen"],
  "spore": "aurora mesh lumen",          // pieni teaser (vapaaehtoinen)
  "beacon_n": 2
}
```

MVP: `entropy_profile`, `tokens_hint` ja `spore` voivat olla tyhjiä / stubbeja.

## Subscription Formaatti (subscriptions.json)
```
{
  "noise_metadata": ["listener-1","listener-xyz"]
}
```
MVP: Jos lista on ei-tyhjä, stream katsoo itsensä attached-tilaan (ensimmäinen havainto riittää).

## State Machine (MVP)
```
idle --------------------> seeking_low ---------------> seeking_escalate --------> shutdown?
  | (listener appears)          | (after escalate_s)            | (after shutdown_s)
  |                             |                               |
  +----------> attached <-------+<------------- subscription ----+
```

- attached: Kun subscription ilmestyy (lista ei tyhjä).
- seeking_low beacon-throttle: ei useammin kuin NOISE_SEEK_BEACON_INTERVAL_LOW_S.
- seeking_escalate beacon-throttle: NOISE_SEEK_BEACON_INTERVAL_ESC_S.

## Loneliness Laskenta
Alkuun yksinkertainen:
```
loneliness_ratio = 1.0 jos delivered_ticks == 0 muutoin max(0, (produced_ticks - delivered_ticks) / max(1, produced_ticks))
```
Myöhemmin: liukuva ikkuna ( viimeiset N tickiä ), delivered signaali oikeista kuluttajista.

## Toimet Tickin Jälkeen (Pseudo)
```
on_tick():
  produced_ticks += 1
  update_state(now)
  beacon = maybe_emit_beacon(now)
  if beacon: append to JSONL
```

## State Päivitys
```
if attached: return
duration = now - first_lonely_ts
if duration >= SHUTDOWN_AFTER: state = seeking_escalate (MVP: log "would shutdown")
elif duration >= ESCALATE_AFTER: state = seeking_escalate
elif duration >= LONELY_AFTER: state = seeking_low
else: state = idle
```

`first_lonely_ts` asetetaan kun havaitaan ettei ole listeneriä.

## Listener Sim (MVP)
Loop:
1. Lataa subscriptions.json (jos puuttuu -> {}).
2. Jos stream_id jo on subscriptionissa -> sleep.
3. Lue beacons.jsonl tail (viimeiset ~200 riviä).
4. Valitse tuorein beacon jossa state alkaa 'seeking_' ja jota ei ole jo tilattu.
5. Lisää itsensä subscription listaan ja kirjoita tiedosto.
6. Print log, sleep.

## Tietoturva / Race (ei MVP:ssä)
Paikallisessa kehityksessä ei tarvita lukituksia. Jos halutaan alustava suoja:
- Kirjoita ensin temp-tiedosto ja `os.replace` atomiseen vaihtoon.
- Beacon append on yleensä ok.

## Laajennus  (Ei vielä MVP)
- Commons Merge: orvot streamit yhdistetään.
- Bandit valinta: listener valitsee beaconit joista on historiallisesti saanut “mielenkiintoisia” entropiaprofiileja.
- Weighted entropia: stream säätää Markov-order tai token_n houkuttelevammaksi.

## TODO (Seeking MVP)
- [ ] Integrate real delivered_ticks update kun kuluttaja oikeasti lukee dataa
- [ ] Entropy profile classification (low / medium / high thresholds)
- [ ] Spore generointi Markov token-joukosta
- [ ] Commons merge logiikka

## Testaus (Tuleva)
- test_seeking_state_progression.py
- test_beacon_rate_limiting.py
- test_subscription_attach.py

## Inspiraatio / Metafora
“Tyhjät metatietokentät eivät ole hiljaisia – ne ovat potentiaalin taskuja. Beacon antaa niille äänen, listener antaa resonanssin.”

---
MVP valmiina kun:
- Beacon rivi syntyy oikeaan aikaan
- Listener_sim lisää subscriptionin
- Stream tunnistaa attached ja lopettaa beaconien lähetyksen

----