# rooms
Doom Taide fork

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