#!/usr/bin/env python3
"""
noise_metadata:
Generates ephemeral "nonsense / filler" metadata events to simulate stream load
without using copyrighted material.

Modes:
  words  - random word buckets
  bytes  - hex-ish byte clusters
  markov - simple Markov chain over an internal seed corpus (tiny, public domain snippet)

Entropy metrics (per event):
  char_len
  char_entropy_avg_bits
  char_entropy_total_bits
  token_count              (words|markov only)
  token_entropy_avg_bits   (words|markov only, unless disabled)
  token_entropy_total_bits (words|markov only, unless disabled)

Env:
  NOISE_MODE=words|bytes|markov (default words)
  NOISE_MIN_INTERVAL (default 0.8)
  NOISE_MAX_INTERVAL (default 2.4)
  NOISE_WORDSET (comma separated override word list)
  NOISE_ENTROPY_BITS (default 128) - reported nominal value
  NOISE_MAX_WORDS (default 8)
  NOISE_DISABLE_TOKEN_ENT (set to any value to skip token entropy)
"""
from __future__ import annotations
import os, time, json, random, datetime, uuid, math, collections

MODE = os.environ.get("NOISE_MODE", "words").lower()
MIN_I = float(os.environ.get("NOISE_MIN_INTERVAL", "0.8"))
MAX_I = float(os.environ.get("NOISE_MAX_INTERVAL", "2.4"))
WORDSET_RAW = os.environ.get("NOISE_WORDSET")
ENTROPY_BITS = int(os.environ.get("NOISE_ENTROPY_BITS", "128"))
MAX_WORDS = int(os.environ.get("NOISE_MAX_WORDS", "8"))
DISABLE_TOKEN_ENT = os.environ.get("NOISE_DISABLE_TOKEN_ENT")
SESSION = uuid.uuid4().hex[:12]

DEFAULT_WORDS = [
    "aurora","flux","drift","lattice","vector","oblique","quantum","slag",
    "orb","haze","spire","mono","delta","prism","ion","fractal","pulse",
    "shard","sable","echo","proto","zenith","phase","morph","grain"
]

if WORDSET_RAW:
    WORDS = [w.strip() for w in WORDSET_RAW.split(",") if w.strip()]
    if not WORDS:
        WORDS = DEFAULT_WORDS
else:
    WORDS = DEFAULT_WORDS

SEED_CORPUS = "flux lattice echo drift aurora phase prism ion shard zenith"

def build_markov(tokens):
    m = {}
    for a, b in zip(tokens, tokens[1:]):
        m.setdefault(a, []).append(b)
    return m

MARKOV_TOKENS = SEED_CORPUS.split()
MARKOV = build_markov(MARKOV_TOKENS)

def markov_sequence(n=MAX_WORDS):
    out = []
    cur = random.choice(MARKOV_TOKENS)
    for _ in range(n):
        out.append(cur)
        nxts = MARKOV.get(cur)
        cur = random.choice(nxts) if nxts else random.choice(MARKOV_TOKENS)
    return out

def gen_text():
    if MODE == "bytes":
        length = random.randint(4, 12)
        return " ".join(
            "".join(random.choice("0123456789abcdef")
                    for _ in range(2 * random.randint(2, 4)))
            for _ in range(length // 2)
        )
    elif MODE == "markov":
        seq = markov_sequence(random.randint(3, MAX_WORDS))
        return " ".join(seq)
    else:
        count = random.randint(3, MAX_WORDS)
        return " ".join(random.choice(WORDS) for _ in range(count))

def shannon_entropy_avg(symbols: list[str]) -> float:
    if not symbols:
        return 0.0
    counter = collections.Counter(symbols)
    total = sum(counter.values())
    h = 0.0
    for c in counter.values():
        p = c / total
        h -= p * math.log2(p)
    return h  # bits per symbol

def entropy_char_metrics(text: str):
    if not text:
        return 0, 0.0, 0.0
    chars = list(text)
    avg = shannon_entropy_avg(chars)
    n = len(chars)
    total = avg * n
    return n, round(avg, 6), round(total, 6)

def entropy_token_metrics(text: str):
    tokens = text.split()
    if not tokens:
        return 0, 0.0, 0.0
    avg = shannon_entropy_avg(tokens)
    n = len(tokens)
    total = avg * n
    return n, round(avg, 6), round(total, 6)

def band_from_interval(i: float) -> str:
    if i < 1.0: return "hf"
    if i < 2.0: return "mf"
    return "lf"

def main():
    print(json.dumps({
        "event": "noise_start",
        "session": SESSION,
        "mode": MODE,
        "entropy_bits": ENTROPY_BITS,
        "ts": datetime.datetime.utcnow().isoformat()
    }), flush=True)
    while True:
        interval = random.uniform(MIN_I, MAX_I)
        time.sleep(interval)
        txt = gen_text()
        char_len, char_avg, char_total = entropy_char_metrics(txt)
        record = {
            "event": "noise_meta",
            "session": SESSION,
            "mode": MODE,
            "seq": int(time.time() * 1000),
            "band": band_from_interval(interval),
            "interval_s": round(interval, 3),
            "entropy_bits": ENTROPY_BITS,
            "char_len": char_len,
            "char_entropy_avg_bits": char_avg,
            "char_entropy_total_bits": char_total,
            "text": txt,
            "ts": datetime.datetime.utcnow().isoformat()
        }
        if MODE in ("words", "markov") and not DISABLE_TOKEN_ENT:
            token_count, token_avg, token_total = entropy_token_metrics(txt)
            record.update({
                "token_count": token_count,
                "token_entropy_avg_bits": token_avg,
                "token_entropy_total_bits": token_total
            })
        print(json.dumps(record, separators=(",", ":")), flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(json.dumps({
            "event": "noise_stop",
            "session": SESSION,
            "ts": datetime.datetime.utcnow().isoformat()
        }), flush=True)