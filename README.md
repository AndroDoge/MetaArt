# rooms
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

## Event payload esimerkit
Alla kolme alustavaa tapahtumatyyppiä. Nimeämiset ja kentät voivat vielä elää.

### noise_start
Lähetetään kerran workerin käynnistyessä (tai uudelleenkäynnistyessä) konfiguraation ilmoittamiseksi.
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
Perus “pulssi” joka kulkee intervalleissa. Sisältää generoidun metadatan ja entropia-arvion.
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
Harvempi “kooste” useasta tickistä; voidaan käyttää analytiikan aggregointiin.
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
- trace_id / run_id jos halutaan linkittää samaan elinkaareen
- payload.encoding jos myöhemmin pakataan (esim. base64, delta)
- stats.noise_level (heuristinen “intensity”)

## Design Principles (Brutalistinen sävy)
Brutalismi tässä: paljastetaan rakenne, karsitaan ornamentti “valmiiksi” – annetaan rytmin ja raakojen arvojen muodostaa tekstuurinsa.

1. Exposed Structure: Konfiguraatio ja event payload pysyvät läpinäkyvinä; ei piilotettua taikaa.
2. Deterministic Core, Stochastic Skin: Ydinlooppi selkeä; variaatio injektoidaan reunoilta parametrein.
3. Composable Pulses: Tick -> Pulse -> (tuleva) Stream; kerrokset modulaarisia.
4. Observability-First: Jokainen merkityksellinen muutos tuottaa mitattavan signaalin (entropy, jitter, burst-score).
5. Constraint as Canvas: Rajoitettu parametriavaruus ohjaa luovuutta; pienet muutokset näkyvät.
6. Playful Defaults: Oletukset tarkoituksella “elävät” mutta hallittavat.
7. Minimal Persistence: Vain se mikä on analytiikalle tai toistettavuudelle välttämätöntä tallennetaan.
8. Data Is Ornament: Ornamentti syntyy numeroiden rytmistä, ei erillisestä koristelusta.
9. Progressive Disclosure: Ensin perus tick, vasta myöhemmin syvemmät Markov/metrics -kerrokset.
10. Cheap to Reset: Koko ympäristö voidaan nollata nopeasti ilman monimutkaista tilansiivousta.

## TODO (elävä lista)
- [x] Event payload esimerkit: `noise_start`, `noise_tick`, `noise_pulse` (schema + sample JSON).
- [x] Design Principles (brutalistinen versio).
- [ ] Ympäristömuuttuja-taulukko selitteillä (määrittele “token” ja “ws” tarkemmin).
- [ ] Markov‑tilasiirtymien dokumentointi + mahdollinen siemenmateriaalin lataus.
- [ ] “Ephemeral streaming” vaihe (rajattu puskurointi ja kulutus).
- [ ] Kevyt metrics: per interval jitter, entropia, burst‑score.
- [ ] ASCII visualisaatio (pieni TUI?) noise-virrasta.
- [ ] Englanninkielinen rinnakkaisosio (README_EN.md tai kaksikieliset otsikot).
- [ ] Roadmap / release tags (v0.1 “Pulse”, v0.2 “Markov Bloom”, ...).
- [ ] Automatisoitu test stub (health check & config validation).
- [ ] Container / image build (Dockerfile + GitHub Actions workflow).

## Filosofia (taidekulma)
“Noise” nähdään tässä raaka‑aineena: ei pelkästään satunnaisuutena vaan rytmin ja rakenteen väreilynä. Tyhjällä kanavalla pienikin kuvio tuntuu merkitykselliseltä – eksplisiittiset funktiot (testisyöte, kuormasimulaatio) lomittuvat esteettiseen tarkasteluun (onko tempo ‘miellyttävä’?).

## (Valinnainen) Jatkokehityksen lisäpalikat
Ehdota / valitse jos haluat lisättäväksi seuraavassa commitissa:
A. Manifesti erilliseksi tiedostoksi (MANIFESTO.md)
B. ASCII‑banneri alkuun
D. Roadmap-kaavio (tekstimuotoinen)
E. Lyhyt “How to contribute jam session” -osio

## Lisenssi
(Täydennä myöhemmin – jos ei vielä päätetty, lisää placeholder.)