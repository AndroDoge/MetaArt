# rooms
```
 ________  ____   ____  ____  ____
/__  ___/ / __ \ / __ \/ __ \/ __ \
  / /    / /_/ // /_/ / /_/ / /_/ /
 / /    / .___/ \__, /\__, /\__, /
/_/    /_/     /____//____//____/
   minimalist pulse & noise lab
```

Doom Taide fork – pieni orkestroitu kokeilulaboratorio jossa “noise” ja muut worker-prosessit tuottavat aineistoa jatkoanalyysille.

## Yleiskuva
Tavoitteena on kevyt orkestrointi: yksi yksinkertainen `orchestrator_tasks.yml` määrittelee käynnistettävät prosessit (workerit). Tällä hetkellä keskiössä on `noise_metadata`, joka generoi pseudo-satunnaista (tai Markov‑ohjattua) metadatalähdettä analytiikan tai testisyötteen tarpeisiin. Projekti on tarkoituksella pieni, iteratiivinen ja vähän taiteellinen: kokeile, tallenna havainnot, muovaa eteenpäin.

## Paikallinen nopea aloitus (Kuinka pääsen “nauttimaan”)
1. Kloonaa repo  
   ```bash
   git clone https://github.com/AndroDoge/rooms.git
   cd rooms
   ```
2. (Valinnainen) Luo erillinen ympäristö (jos käytät Python‑/Node‑työkaluja tms. myöhemmin).  
3. Aja suoraan noise‑worker (jos `start.sh` on suoritusoikeuksilla):  
   ```bash
   ./start.sh noise_metadata
   ```  
   Jos tarvitset ympäristömuuttujia eri arvoilla:  
   ```bash
   NOISE_INTERVAL_S=1.5 NOISE_MODE=markov ./start.sh noise_metadata
   ```
4. Tarkkaile outputtia (esim.):  
   ```bash
   tail -f logs/noise_metadata.log
   # tai
   journalctl -f -u noise_metadata.service  # jos systemd-yksikkö myöhemmin
   ```
5. Iteroi arvoja “tuntumalla”: nosta tai laske intervalleja ja katso miten rytmi elää.
6. (Kokeellinen) Voit simuloida “pulssin” häiriötä:  
   ```bash
   NOISE_MIN_INTERVAL_S=0.2 NOISE_MAX_INTERVAL_S=3.5 NOISE_DEBUG=1 ./start.sh noise_metadata
   ```
7. Lopeta prosessi hallitusti: Ctrl+C (tai lähetä SIGTERM jos demonisoitu).

Vinkkejä nautiskeluun:
- Kirjoita pieni sivuskripti joka laskee entropiaa rivivirrasta ja visualisoi (esim. ASCII‑sparklines).
- Vertaa eri MODE‑arvojen (tulevat) rytmisiä profiileja.
- Sekoita parametreja “Rorschach”-henkisesti ja tallenna miellyttävät presetit.

## orchestrator_tasks.yml esimerkkikonfiguraatio
```yaml
# orchestrator_tasks.yml
tasks:
  - name: noise_metadata
    type: process
    command: |
      ./start.sh noise_metadata
    env:
      NOISE_INTERVAL_S: "2.5"
      NOISE_MIN_INTERVAL_S: "1.0"
      NOISE_MAX_INTERVAL_S: "4.0"
      NOISE_MODE: "markov"
      # NOISE_MARKOV_SEED: "42"
      NOISE_MIN_WS: "30"
      NOISE_MAX_WS: "120"
      NOISE_MAX_LEN: "320"
      NOISE_MAX_TOKEN_N: "5"
      NOISE_DEBUG: "0"
    resources:
      cpu: "50m"
      memory: "64Mi"
    restart_policy: on-failure
    max_restarts: 3
```

## Ympäristömuuttujat (A)
| Nimi | Tyyppi | Oletus (ehdotettu) | Kuvaus | Rajoite / Huom |
|------|-------|--------------------|--------|----------------|
| NOISE_INTERVAL_S | float | 2.5 | Keski-intervalli sekunteina, jos kiinteä (käytetään kun min/max ei annettu tai kun halutaan vakio) | > 0 |
| NOISE_MIN_INTERVAL_S | float | 1.0 | Satunnaisen/jitteroidun intervallin minimi (sek) | 0 < min < max |
| NOISE_MAX_INTERVAL_S | float | 4.0 | Satunnaisen/jitteroidun intervallin maksimi (sek) | max > min |
| NOISE_MODE | enum | markov | Generointimoodi: `basic`, `markov`, (tuleva) `chain2`, `burst` | Laajenee |
| NOISE_MARKOV_SEED | int | (tyhjä) | Siemen deterministiseen Markov-ketjun valintaan | Jos tyhjä → ei determinismiä |
| NOISE_MIN_WS | int | 30 | Sliding window (ws) pienin koko statistiikkaan (esim. entropia) | >= 1 |
| NOISE_MAX_WS | int | 120 | Sliding window suurin koko; voi kasvaa dynaamisesti | >= MIN_WS |
| NOISE_MAX_LEN | int | 320 | Yhden tuotetun merkkijonon maksimipituus merkkeinä | > 0 |
| NOISE_MAX_TOKEN_N | int | 5 | Maksimitokenien määrä per tick payload | > 0 |
| NOISE_DEBUG | bool/int | 0 | Lisälogging: 0=pois, 1=päälinjat, 2=verbose | Ei tuotantoon korkeilla arvoilla |
| NOISE_ENTROPY_BASE | int | 256 | (Ehdotus) Entropialaskennan symboliavaruus / normalisointi | Kehittyy |
| NOISE_PULSE_INTERVAL_TICKS | int | 30 | Kuinka monen tickin jälkeen muodostetaan pulse-kooste | > 0 |
| NOISE_JITTER_MODE | enum | uniform | Jitter-lähde: `uniform`, `triangular`, (tuleva) `exp` | Vaikuttaa ajoitukseen |
| NOISE_OUTPUT_FORMAT | enum | jsonl | Tulostusformaatti: `jsonl`, `ndjson`, (tuleva) `msgpack` | Työpohjainen |
| NOISE_PAYLOAD_ALPHABET | str | (sisäinen) | Merkkiryhmä jonka pohjalta basic-moodi arpoo | Markov ohittaa |

Huom: ws = window size analytiikkaan (esim. entropialaskennan joustava näytealue).

## Markov-tilasiirtymät (B)
Markov-moodi käyttää n-gram -pohjaista ketjua (oletuksena n=2 tai n=3). Tavoite: rytmisen “melkein-toistettavan” mutta vaihtelevan token-joukon generointi.

Perusmalli:
1. Sanasto muodostetaan siemenmateriaalista (tekstitiedosto / sisäänrakennettu lista).
2. Siirtymätaulukko rakennetaan laskemalla esiintymät:
   ```
   P(next = t_k | prev = t_i) = count(t_i -> t_k) / Σ_j count(t_i -> t_j)
   ```
3. Jos `NOISE_MARKOV_SEED` asetettu, valitaan deterministinen siemen RNG:lle (esim. PCG).
4. Backoff: Jos polku puuttuu (harvinainen n-gram), fallback pienempään n:ään tai uniform-satunnaisuuteen sanastosta.
5. Token-valinnan jälkeen kerätään entropia ja tallennetaan payloadiin.

Esimerkkisiirtymä (JSON luonnos):
```json
{
  "order": 2,
  "states": {
    "aurora mesh": { "lumen": 4, "pulse": 2 },
    "mesh lumen": { "veil": 3, "aurora": 1 }
  },
  "totals": {
    "aurora mesh": 6,
    "mesh lumen": 4
  }
}
```

Generointialgoritmi (korkean tason pseudokoodi):
```
state = initial_state()
tokens = []
while len(tokens) < NOISE_MAX_TOKEN_N and char_len < NOISE_MAX_LEN:
    next = sample( states[state] ) with RNG(seed?)
    tokens.append(next)
    state = shift_and_append(state, next)
```

Mahdolliset laajennukset:
- Painotettu pulssi: säädä todennäköisyys jakamalla paino entropiafeedbackilla.
- Burst-moodi: kasvattaa token_n tilapäisesti kun entropia laskee alle kynnysarvon.

### Siemenmateriaalin lataus
- `data/markov_seed.txt` (plain UTF-8) → käsitellään tokenisoimalla whitespace + peruspuhdistus.
- Vaihtoehtoisesti `data/markov_seed.json` jossa { "tokens": ["aurora","mesh","..."] }.

### Deterministinen toisto
Jos haluat uudelleentoistettavan sarjan:
```
NOISE_MODE=markov NOISE_MARKOV_SEED=42 NOISE_INTERVAL_S=2.0 ./start.sh noise_metadata
```
Tuloksena identtinen token-jono (olettaen identtiset seed-materiaalit ja versiot).

## Event payload esimerkit
(Entiset esimerkit – ei muutosta tässä vaiheessa.)

### noise_start
```json
{
  "event": "noise_start",
  "ts": "2025-08-28T19:45:12.123Z",
  "version": 1,
  "mode": "markov",
  "interval_s": 2.5,
  "min_interval_s": 1.0,
  "max_interval_s": 4.0,
  "min_ws": 30,
  "max_ws": 120,
  "max_len": 320,
  "max_token_n": 5,
  "debug": false,
  "markov_seed": 42
}
```

### noise_tick
```json
{
  "event": "noise_tick",
  "ts": "2025-08-28T19:45:14.701Z",
  "seq": 17,
  "dt_since_prev_ms": 2487,
  "mode": "markov",
  "payload": {
    "tokens": ["aurora", "mesh", "lumen"],
    "raw": "aurora mesh lumen",
    "token_n": 3,
    "char_len": 18
  },
  "stats": {
    "entropy_bits_per_char": 3.74,
    "entropy_bits_total": 67.3,
    "jitter_ms": 13,
    "window_size": 78
  }
}
```

### noise_pulse
```json
{
  "event": "noise_pulse",
  "ts": "2025-08-28T19:50:00.003Z",
  "seq_start": 120,
  "seq_end": 149,
  "tick_count": 30,
  "interval_stats": {
    "avg_ms": 2510.4,
    "min_ms": 2461,
    "max_ms": 2598,
    "p95_ms": 2555
  },
  "entropy_stats": {
    "avg_bits_per_char": 3.69,
    "avg_bits_total": 65.8,
    "max_bits_total": 72.1
  },
  "mode": "markov"
}
```

Kenttäideoita jatkoon:
- trace_id / run_id
- payload.encoding
- stats.noise_level

## Seeking / Self-Seeking Streams (Experimentaalinen)
Stream voi etsiä kuulijaa jos sitä ei kuunnella: “loneliness” (tuotetut vs. toimitetut) kasvaa -> beaconit JSON:iin -> listener-simulaatio poimii. Katso: [docs/SEEKING.md](./docs/SEEKING.md). Roadmap: v0.35–0.37.

## Design Principles (Brutalistinen sävy)
Brutalismi tässä: paljastetaan rakenne, karsitaan ornamentti “valmiiksi” – annetaan rytmin ja raakojen arvojen muodostaa tekstuurinsa.

1. Exposed Structure
2. Deterministic Core, Stochastic Skin
3. Composable Pulses
4. Observability-First
5. Constraint as Canvas
6. Playful Defaults
7. Minimal Persistence
8. Data Is Ornament
9. Progressive Disclosure
10. Cheap to Reset

## Roadmap (C)
```
v0.1  Pulse             : Perus tick + pulse, entropy & jitter (DONE / nearly)
v0.2  Markov Bloom      : Markov order2, seed-lataus, deterministinen toisto
v0.3  Observability Mesh: Laajennetut metrics (burst-score, jitter histogram)
v0.35 Seeking Presence  : Loneliness counter + beacon JSON MVP
v0.36 Listener Adapter  : listener_sim.py (perus match)
v0.37 Commons Merge     : Orpojen yhdistyminen 'commons' feediksi
v0.4  Stream Ephemera   : Ephemeral buffer + kulutusrajapinta
v0.5  TUI Entropy Scope : ASCII/TUI visualisaatio + interaktiivinen säätö
v0.6  Container & CI     : Dockerfile, GitHub Actions, health checks
v0.7  Multi-Mode Fusion  : Burst / chain2 / adaptive intervals
v0.8  Encoding Layer     : Payload compression / msgpack / delta
v0.9  API / SDK          : Kuluttaja-rajapinta (pipe, unix socket, HTTP SSE)
v1.0  Brutalist Core     : Vakaa interface + dokumentoitu contract
```

Milestone-kriteerit:
- “Valmis” = spesifikaatio & test stub & dokumentaatio osuudelle.

## Filosofia (taidekulma)
“Noise” nähdään tässä raaka‑aineena: ei pelkästään satunnaisuutena vaan rytmin ja rakenteen väreilynä. Tyhjällä kanavalla pienikin kuvio tuntuu merkitykselliseltä – eksplisiittiset funktiot (testisyöte, kuormasimulaatio) lomittuvat esteettiseen tarkasteluun (onko tempo ‘miellyttävä’?).

## Manifesto (E)
Katso: [MANIFESTO.md](./MANIFESTO.md)

## TODO (päivitetty)
- [x] Event payload esimerkit: `noise_start`, `noise_tick`, `noise_pulse`
- [x] Design Principles (brutalistinen versio)
- [x] Ympäristömuuttuja-taulukko selitteillä
- [x] Markov-tilasiirtymien dokumentointi (perus luonnos)
- [x] Roadmap (tekstikaavio)
- [x] Manifesto erilleen
- [ ] Ephemeral streaming buffer
- [ ] Laajennetut metrics: burst-score, jitter histogram
- [ ] ASCII visualisaatio / TUI
- [ ] Englanninkielinen rinnakkaisosio (README_EN.md)
- [ ] Test stub (health check & config validation)
- [ ] Container / image build (Dockerfile + GitHub Actions)
- [ ] Payload encoding / msgpack / delta (roadmap v0.8)
- [ ] API / SDK (roadmap v0.9)
- [ ] Lisenssin tarkistus (MIT ok? Vaihto tarvittaessa)
- [ ] Seeking: loneliness counter coreen (v0.35)
- [ ] Seeking: beacon JSON kirjoitus (v0.35)
- [ ] Listener sim: basic subscription (v0.36)
- [ ] Commons merge experiment (v0.37)

## (Valinnainen) Jatkokehityksen lisäpalikat
A. Manifesti (tehty)  
B. ASCII‑banneri (tehty)  
D. Roadmap-kaavio (tehty)  
E. “How to contribute jam session” (tulossa)

## How to Contribute (luonnos)
Tulossa: “jam session” -ohje interaktiiviseen parameter-playhun (v0.5 yhteydessä).

## Lisenssi (F)
Katso LICENSE (MIT). Voit muuttaa ennen ensimmäistä tagia.