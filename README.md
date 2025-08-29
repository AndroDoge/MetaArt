# rooms
Noise you can't hear

Tämä fork sisältää kokeellisen "orchestrator + adaptiiviset workerit" -mallin, jossa eri prosessit käynnistyvät tai sammuvat websocket-klienttien määrän ja hiljaisuustilan (quiet mode) perusteella.

## Rakenteen Ydin

- Orchestrator (erillinen prosessi / skripti; ei vielä avattu tässä tiedostossa) lukee `orchestrator_tasks.yml` ja käynnistää konfiguroidut workerit.
- Jokaisella workerilla on:
  - restart-politikka (backoff)
  - min_ws_clients / max_ws_clients -rajat
  - hysteresis (estää "läpättämisen" raja-arvon ympärillä)
  - ignore_quiet: jos false -> quiet-tilassa pysäytetään.

## Nykyiset Workerit

| Task             | Tarkoitus                                    | Aktivaatio                               | Quiet Mode |
|------------------|-----------------------------------------------|-------------------------------------------|------------|
| discovery_probe  | Harvat presence/probe JSON-sykäykset          | min_ws=0, pysähtyy kun >1 (max_ws=1)      | Jatkaa (ignore_quiet) |
| topic1_worker    | topic1 create/delete -demolooppi              | Aina (min_ws=0)                           | Jatkaa (ignore_quiet) |
| analysis_phase   | Liukuva ikkuna ja tilastot topic1:stä         | min_ws=2 (10s summaryt)                   | Pysähtyy   |
| noise_metadata   | Kohina/höpönlöpö metadata -stream             | min_ws=0 (tai säädettävissä)              | Jatkaa     |

Lisää "all_in_stage" voidaan aktivoida myöhemmin (kommentoitu mallina).

## analysis_phase Output

Tulostaa (oletus 10s välein):
```
{"topic":"topic1","event":"summary","window_s":30.0,"summary_interval_s":10.0,"creates":N,"deletes":M,"live":(N-M),"ts":"```

Ympäristömuuttujat:
- ANALYSIS_WINDOW_S (default 30)
- ANALYSIS_SUMMARY_INTERVAL (default 10)

## discovery_probe Output

Satunnaisvälein (5–15s, jitter):
```
{"event":"probe","session":"```

Override:
- PROBE_MIN_INTERVAL
- PROBE_MAX_INTERVAL
- PROBE_JITTER

## noise_metadata (kohina / metadataläppä) + ENTROPY

Generoi "sisällötöntä" / public-domain -henkistä pseudometadataa. Tavoite:
- Täyttää streamia ilman tekijänoikeusriskiä
- Ei tallenna levyyn (vain stdout)
- Vaihtuvat moodit: words | bytes | markov

Esimerkkirivi (mode=words):
```
{
  "event":"noise_meta",
  "session":"```

Kentät:
- entropy_bits: konfiguroitu nimellinen arvo (ei laskennallinen).
- char_len: rivin text pituus merkkeinä (välilyönnit mukana).
- char_entropy_avg_bits: Shannon H (bits per char).
- char_entropy_total_bits: avg * char_len.
- token_count: tokenien määrä (mode words|markov).
- token_entropy_avg_bits: Shannon H (bits per token).
- token_entropy_total_bits: avg * token_count.
- token_* kentät puuttuvat mode=bytes.
- Voit disabloida token-entropian asettamalla NOISE_DISABLE_TOKEN_ENT.

Ympäristömuuttujat:
- NOISE_MIN_INTERVAL / NOISE_MAX_INTERVAL
- NOISE_WORDSET
- NOISE_ENTROPY_BITS
- NOISE_MODE (words|bytes|markov)
- NOISE_MAX_WORDS
- NOISE_DISABLE_TOKEN_ENT

## Ephemeral Streaming (tuleva PR)

Suunnitelma:
- Sidecar WS (FastAPI / uvicorn)
- In-memory broadcast
- Lyhytikäiset tokenit, `Cache-Control: no-store`
- Ei raakatekstiä jos ei varmaa public domainia

## Turvallisuus & Eristys

Suosituksia jatkoon:
- Process group (setsid) per worker
- Rate limit restarteille
- Health ping vs. silent fail detection
- Crash logi erilliseen tiedostoon (tai ring buffer)

## Secret Scan Workflow

`.github/workflows/secret-scan.yml`:
- Ajastettu 01:20 UTC
- Quick "no history" + scheduled full history SARIF

## Kehitys

Asennus (esimerkki):
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Käynnistä (orchestrator placeholder):
```
python orchestrator.py
```

Seuraa lokia:
```
tail -f logs/*.log
```

## Lisenssi

(Täydennä projektin lisenssiehdot tähän jos puuttuu.)

## TODO (seuraavat PR:t)

- Ephemeral streaming sidecar
- Restart flood guard
- /metrics ja /health
- all_in_stage worker
- Markov2 / bigram dropout

----
Codename: bits_syndicatium_inexcelsis_deo
