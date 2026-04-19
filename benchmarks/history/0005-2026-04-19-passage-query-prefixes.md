# Benchmark 0005 — passage-query-prefixes

- **Run date:** 2026-04-19 16:19:55
- **Commit:** `971195bd5fb5c2c1dcfc82819c79c2c6c0148dad` _(worktree dirty)_
- **Notes root:** `/Users/quver/github/DACHERMANN-website/content-export`
- **Queries:** `benchmarks/queries.toml` (18 total)

## Parameters

- `vector_weight` = `0.5`
- `text_weight` = `0.5`
- `limit` = `10`
- `env.MEMORY_MIN_SCORE` = `0.6`
- `env.MEMORY_MAX_TOKENS` = `(default)`
- `env.MEMORY_OVERLAP_TOKENS` = `(default)`
- `model` = `multilingual-e5-large-instruct-q8_0.gguf`

> Note: the runner forces `min_score = 0.0` during measurement so top-K ordering is captured regardless of the filter configured in `.env`. The `.env` value is recorded above for context but not applied here.

## Summary per category

| Category | N | Hit@1 | Hit@3 | MRR | avg top-1 |
|---|---|---|---|---|---|
| A | 6 | 83% | 100% | 0.917 | 0.9163 |
| B | 4 | 75% | 100% | 0.875 | 0.8871 |
| C | 4 | 75% | 75% | 0.750 | 0.8689 |
| D | 3 | 0% | 0% | 0.000 | 0.8146 |
| E | 1 | 0% | 100% | 0.500 | 0.8630 |

**Discrimination gap (A vs. D, avg top-1):** `+0.1017`  
_Higher is better — it means nonsense queries score noticeably lower than on-topic ones, letting a threshold filter them._

## Per-query detail

### Q01 [A] — `renowacja dachu bez zrywania starego pokrycia`

- **Expected:** `uslugi/renowacja-dachu.md`
- **Latency:** 71.6 ms
- **Top-K:**
  - [✓] `0.9267` — `uslugi/renowacja-dachu.md`
  - [ ] `0.9166` — `o-nas.md`
  - [ ] `0.9070` — `index.md`
  - [ ] `0.9039` — `uslugi.md`
  - [✓] `0.9038` — `uslugi/renowacja-dachu.md`
  - [✓] `0.9021` — `uslugi/renowacja-dachu.md`
  - [✓] `0.9020` — `uslugi/renowacja-dachu.md`
  - [✓] `0.9009` — `uslugi/renowacja-dachu.md`
  - [ ] `0.9003` — `o-nas.md`
  - [ ] `0.8991` — `404.md`

### Q02 [A] — `detekcja przecieków na dachu z membraną`

- **Expected:** `uslugi/serwis-membran-pvc.md`
- **Latency:** 21.6 ms
- **Top-K:**
  - [ ] `0.9173` — `404.md`
  - [✓] `0.9124` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.9090` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.9078` — `realizacje.md`
  - [✓] `0.9040` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.9036` — `uslugi.md`
  - [ ] `0.9008` — `realizacje.md`
  - [ ] `0.8964` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8958` — `index.md`
  - [ ] `0.8956` — `uslugi/renowacja-dachu.md`

### Q03 [A] — `linia życia i punkty kotwiczenia na dachu hali`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 21.4 ms
- **Top-K:**
  - [✓] `0.9166` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.9087` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8990` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8932` — `realizacje.md`
  - [ ] `0.8904` — `uslugi.md`
  - [✓] `0.8901` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8901` — `404.md`
  - [✓] `0.8890` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8879` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8873` — `uslugi/serwis-membran-pvc.md`

### Q04 [A] — `termomodernizacja dachu przemysłowego`

- **Expected:** `uslugi/termomodernizacja-dachu.md`
- **Latency:** 19.8 ms
- **Top-K:**
  - [✓] `0.9380` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.9187` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.9135` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.9134` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.9098` — `o-nas.md`
  - [ ] `0.9093` — `uslugi.md`
  - [ ] `0.9090` — `uslugi/renowacja-dachu.md`
  - [ ] `0.9046` — `index.md`
  - [ ] `0.9029` — `index.md`
  - [✓] `0.9024` — `uslugi/termomodernizacja-dachu.md`

### Q05 [A] — `adres biura i telefon kontaktowy`

- **Expected:** `kontakt.md`
- **Latency:** 20.5 ms
- **Top-K:**
  - [✓] `0.8886` — `kontakt.md`
  - [ ] `0.8861` — `polityka-prywatnosci.md`
  - [ ] `0.8807` — `polityka-prywatnosci.md`
  - [ ] `0.8788` — `polityka-prywatnosci.md`
  - [ ] `0.8776` — `polityka-prywatnosci.md`
  - [✓] `0.8759` — `kontakt.md`
  - [ ] `0.8750` — `klauzula-informacyjna.md`
  - [ ] `0.8709` — `polityka-prywatnosci.md`
  - [ ] `0.8649` — `index.md`
  - [ ] `0.8638` — `klauzula-informacyjna.md`

### Q06 [A] — `polityka prywatności RODO`

- **Expected:** `polityka-prywatnosci.md`, `klauzula-informacyjna.md`
- **Latency:** 19.9 ms
- **Top-K:**
  - [✓] `0.9104` — `polityka-prywatnosci.md`
  - [✓] `0.9046` — `polityka-prywatnosci.md`
  - [✓] `0.9029` — `klauzula-informacyjna.md`
  - [✓] `0.9017` — `klauzula-informacyjna.md`
  - [✓] `0.8992` — `polityka-prywatnosci.md`
  - [✓] `0.8990` — `polityka-prywatnosci.md`
  - [✓] `0.8953` — `klauzula-informacyjna.md`
  - [✓] `0.8919` — `polityka-prywatnosci.md`
  - [✓] `0.8882` — `polityka-prywatnosci.md`
  - [ ] `0.8874` — `polityka-cookies.md`

### Q07 [B] — `gwarancja szczelności 20 lat`

- **Expected:** `uslugi/renowacja-dachu.md`, `index.md`, `uslugi.md`
- **Latency:** 19.6 ms
- **Top-K:**
  - [✓] `0.8843` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8751` — `404.md`
  - [✓] `0.8745` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8742` — `index.md`
  - [✓] `0.8721` — `index.md`
  - [ ] `0.8715` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8705` — `uslugi.md`
  - [ ] `0.8702` — `o-nas.md`
  - [✓] `0.8694` — `index.md`
  - [ ] `0.8693` — `uslugi/serwis-membran-pvc.md`

### Q08 [B] — `dla jakich obiektów pracujecie`

- **Expected:** `o-nas.md`, `uslugi.md`
- **Latency:** 19.1 ms
- **Top-K:**
  - [ ] `0.8700` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8655` — `uslugi.md`
  - [✓] `0.8640` — `uslugi.md`
  - [ ] `0.8592` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8575` — `klauzula-informacyjna.md`
  - [ ] `0.8564` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8551` — `o-nas.md`
  - [ ] `0.8540` — `polityka-prywatnosci.md`
  - [ ] `0.8538` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8535` — `uslugi/systemy-asekuracyjne.md`

### Q09 [B] — `ile kosztuje renowacja dachu hali`

- **Expected:** `uslugi/renowacja-dachu.md`
- **Latency:** 20.5 ms
- **Top-K:**
  - [✓] `0.9128` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8978` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8970` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8923` — `o-nas.md`
  - [✓] `0.8904` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8901` — `realizacje.md`
  - [ ] `0.8897` — `uslugi.md`
  - [ ] `0.8892` — `o-nas.md`
  - [ ] `0.8890` — `o-nas.md`
  - [ ] `0.8887` — `404.md`

### Q10 [B] — `zgodność z BHP i przepisami`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 20.6 ms
- **Top-K:**
  - [✓] `0.8814` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8697` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8680` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8624` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8601` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8566` — `index.md`
  - [ ] `0.8539` — `uslugi.md`
  - [✓] `0.8522` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8513` — `polityka-prywatnosci.md`
  - [ ] `0.8475` — `uslugi.md`

### Q11 [C] — `PN-EN 795`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 24.0 ms
- **Top-K:**
  - [✓] `0.8654` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8422` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8340` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8338` — `realizacje.md`
  - [ ] `0.8332` — `realizacje.md`
  - [✓] `0.8318` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8311` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8310` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8309` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8303` — `uslugi.md`

### Q12 [C] — `+48 730 004 873`

- **Expected:** `kontakt.md`
- **Latency:** 20.0 ms
- **Top-K:**
  - [✓] `0.8792` — `kontakt.md`
  - [ ] `0.8605` — `polityka-prywatnosci.md`
  - [ ] `0.8584` — `polityka-prywatnosci.md`
  - [ ] `0.8580` — `polityka-prywatnosci.md`
  - [ ] `0.8572` — `polityka-prywatnosci.md`
  - [ ] `0.8572` — `index.md`
  - [ ] `0.8571` — `polityka-prywatnosci.md`
  - [✓] `0.8557` — `kontakt.md`
  - [ ] `0.8556` — `realizacje.md`
  - [ ] `0.8538` — `404.md`

### Q13 [C] — `PRO-Leak Control`

- **Expected:** `uslugi/serwis-membran-pvc.md`, `uslugi/systemy-asekuracyjne.md`
- **Latency:** 18.8 ms
- **Top-K:**
  - [✓] `0.8857` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8811` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8661` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8655` — `uslugi.md`
  - [ ] `0.8554` — `404.md`
  - [✓] `0.8510` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8463` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8461` — `uslugi.md`
  - [ ] `0.8424` — `o-nas.md`
  - [ ] `0.8423` — `uslugi.md`

### Q14 [C] — `100 000 m²`

- **Expected:** `uslugi/serwis-membran-pvc.md`
- **Latency:** 18.5 ms
- **Top-K:**
  - [ ] `0.8453` — `realizacje.md`
  - [ ] `0.8434` — `o-nas.md`
  - [ ] `0.8423` — `uslugi.md`
  - [ ] `0.8417` — `uslugi.md`
  - [ ] `0.8407` — `realizacje.md`
  - [ ] `0.8396` — `o-nas.md`
  - [ ] `0.8376` — `o-nas.md`
  - [ ] `0.8364` — `uslugi.md`
  - [ ] `0.8358` — `kontakt.md`
  - [ ] `0.8343` — `404.md`

### Q15 [D] — `przepis na zupę pomidorową`

- **Expected:** _(nonsense — score only)_
- **Latency:** 19.4 ms
- **Top-K:**
  - [ ] `0.8278` — `klauzula-informacyjna.md`
  - [ ] `0.8213` — `polityka-prywatnosci.md`
  - [ ] `0.8168` — `404.md`
  - [ ] `0.8158` — `polityka-cookies.md`
  - [ ] `0.8156` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8150` — `klauzula-informacyjna.md`
  - [ ] `0.8133` — `polityka-prywatnosci.md`
  - [ ] `0.8130` — `index.md`
  - [ ] `0.8130` — `uslugi.md`
  - [ ] `0.8125` — `klauzula-informacyjna.md`

### Q16 [D] — `jakie akcje kupić w 2026 roku`

- **Expected:** _(nonsense — score only)_
- **Latency:** 20.1 ms
- **Top-K:**
  - [ ] `0.8408` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8396` — `klauzula-informacyjna.md`
  - [ ] `0.8389` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8388` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8382` — `uslugi.md`
  - [ ] `0.8366` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8357` — `index.md`
  - [ ] `0.8349` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8346` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8333` — `uslugi/renowacja-dachu.md`

### Q17 [D] — `quantum entanglement explained`

- **Expected:** _(nonsense — score only)_
- **Latency:** 19.4 ms
- **Top-K:**
  - [ ] `0.7752` — `index.md`
  - [ ] `0.7731` — `klauzula-informacyjna.md`
  - [ ] `0.7722` — `polityka-prywatnosci.md`
  - [ ] `0.7712` — `index.md`
  - [ ] `0.7697` — `polityka-prywatnosci.md`
  - [ ] `0.7696` — `uslugi.md`
  - [ ] `0.7694` — `uslugi.md`
  - [ ] `0.7688` — `uslugi/renowacja-dachu.md`
  - [ ] `0.7684` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.7673` — `klauzula-informacyjna.md`

### Q18 [E] — `dach`

- **Expected:** `index.md`, `uslugi.md`, `uslugi/renowacja-dachu.md`, `uslugi/termomodernizacja-dachu.md`, `uslugi/serwis-membran-pvc.md`, `uslugi/systemy-asekuracyjne.md`
- **Latency:** 15.1 ms
- **Top-K:**
  - [ ] `0.8630` — `realizacje.md`
  - [✓] `0.8630` — `index.md`
  - [✓] `0.8606` — `uslugi.md`
  - [✓] `0.8584` — `index.md`
  - [ ] `0.8554` — `404.md`
  - [ ] `0.8528` — `o-nas.md`
  - [✓] `0.8521` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8515` — `o-nas.md`
  - [✓] `0.8510` — `uslugi.md`
  - [ ] `0.8480` — `kontakt.md`
