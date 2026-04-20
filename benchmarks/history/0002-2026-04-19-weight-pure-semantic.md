# Benchmark 0002 — weight-pure-semantic

- **Run date:** 2026-04-19 15:39:14
- **Commit:** `971195bd5fb5c2c1dcfc82819c79c2c6c0148dad` _(worktree dirty)_
- **Notes root:** `/Users/quver/github/DACHERMANN-website/content-export`
- **Queries:** `benchmarks/queries.toml` (18 total)

## Parameters

- `vector_weight` = `1.0`
- `text_weight` = `0.0`
- `limit` = `10`
- `env.MEMORY_MIN_SCORE` = `0.6`
- `env.MEMORY_MAX_TOKENS` = `(default)`
- `env.MEMORY_OVERLAP_TOKENS` = `(default)`
- `model` = `multilingual-e5-large-instruct-q8_0.gguf`

> Note: the runner forces `min_score = 0.0` during measurement so top-K ordering is captured regardless of the filter configured in `.env`. The `.env` value is recorded above for context but not applied here.

## Summary per category

| Category | N | Hit@1 | Hit@3 | MRR | avg top-1 |
|---|---|---|---|---|---|
| A | 6 | 83% | 100% | 0.889 | 0.9840 |
| B | 4 | 75% | 100% | 0.875 | 0.8827 |
| C | 4 | 75% | 75% | 0.750 | 0.9877 |
| D | 3 | 0% | 0% | 0.000 | 0.8180 |
| E | 1 | 100% | 100% | 1.000 | 1.0412 |

**Discrimination gap (A vs. D, avg top-1):** `+0.1660`  
_Higher is better — it means nonsense queries score noticeably lower than on-topic ones, letting a threshold filter them._

## Per-query detail

### Q01 [A] — `renowacja dachu bez zrywania starego pokrycia`

- **Expected:** `uslugi/renowacja-dachu.md`
- **Latency:** 70.5 ms
- **Top-K:**
  - [✓] `1.4112` — `uslugi/renowacja-dachu.md`
  - [ ] `1.2764` — `index.md`
  - [✓] `1.1486` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8908` — `o-nas.md`
  - [✓] `0.8890` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8888` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8888` — `404.md`
  - [✓] `0.8874` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8874` — `o-nas.md`
  - [ ] `0.8867` — `uslugi.md`

### Q02 [A] — `detekcja przecieków na dachu z membraną`

- **Expected:** `uslugi/serwis-membran-pvc.md`
- **Latency:** 23.8 ms
- **Top-K:**
  - [ ] `0.9019` — `realizacje.md`
  - [ ] `0.9017` — `404.md`
  - [✓] `0.8976` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8961` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8899` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8891` — `uslugi.md`
  - [ ] `0.8884` — `realizacje.md`
  - [ ] `0.8865` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8850` — `index.md`
  - [ ] `0.8831` — `uslugi/renowacja-dachu.md`

### Q03 [A] — `linia życia i punkty kotwiczenia na dachu hali`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 24.9 ms
- **Top-K:**
  - [✓] `0.9016` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8943` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8865` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8817` — `realizacje.md`
  - [ ] `0.8782` — `404.md`
  - [✓] `0.8779` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8768` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8760` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8756` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8755` — `uslugi.md`

### Q04 [A] — `termomodernizacja dachu przemysłowego`

- **Expected:** `uslugi/termomodernizacja-dachu.md`
- **Latency:** 21.7 ms
- **Top-K:**
  - [✓] `0.9110` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8927` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8907` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8882` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8864` — `index.md`
  - [ ] `0.8849` — `index.md`
  - [ ] `0.8843` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8841` — `realizacje.md`
  - [ ] `0.8841` — `o-nas.md`
  - [ ] `0.8816` — `uslugi.md`

### Q05 [A] — `adres biura i telefon kontaktowy`

- **Expected:** `kontakt.md`
- **Latency:** 15.8 ms
- **Top-K:**
  - [✓] `0.8796` — `kontakt.md`
  - [ ] `0.8702` — `polityka-prywatnosci.md`
  - [ ] `0.8694` — `polityka-prywatnosci.md`
  - [ ] `0.8663` — `polityka-prywatnosci.md`
  - [✓] `0.8652` — `kontakt.md`
  - [ ] `0.8631` — `klauzula-informacyjna.md`
  - [ ] `0.8604` — `polityka-prywatnosci.md`
  - [ ] `0.8585` — `index.md`
  - [ ] `0.8584` — `polityka-prywatnosci.md`
  - [ ] `0.8574` — `polityka-prywatnosci.md`

### Q06 [A] — `polityka prywatności RODO`

- **Expected:** `polityka-prywatnosci.md`, `klauzula-informacyjna.md`
- **Latency:** 18.4 ms
- **Top-K:**
  - [✓] `0.8987` — `polityka-prywatnosci.md`
  - [✓] `0.8942` — `polityka-prywatnosci.md`
  - [✓] `0.8935` — `polityka-prywatnosci.md`
  - [✓] `0.8919` — `klauzula-informacyjna.md`
  - [✓] `0.8887` — `polityka-prywatnosci.md`
  - [✓] `0.8872` — `klauzula-informacyjna.md`
  - [✓] `0.8829` — `klauzula-informacyjna.md`
  - [✓] `0.8827` — `polityka-prywatnosci.md`
  - [✓] `0.8805` — `polityka-prywatnosci.md`
  - [✓] `0.8801` — `polityka-prywatnosci.md`

### Q07 [B] — `gwarancja szczelności 20 lat`

- **Expected:** `uslugi/renowacja-dachu.md`, `index.md`, `uslugi.md`
- **Latency:** 18.5 ms
- **Top-K:**
  - [✓] `0.8741` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8731` — `uslugi.md`
  - [✓] `0.8672` — `index.md`
  - [ ] `0.8663` — `o-nas.md`
  - [ ] `0.8661` — `404.md`
  - [✓] `0.8638` — `index.md`
  - [✓] `0.8635` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8635` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8631` — `index.md`
  - [✓] `0.8629` — `uslugi.md`

### Q08 [B] — `dla jakich obiektów pracujecie`

- **Expected:** `o-nas.md`, `uslugi.md`
- **Latency:** 14.3 ms
- **Top-K:**
  - [ ] `0.8688` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8646` — `uslugi.md`
  - [ ] `0.8593` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8591` — `uslugi.md`
  - [ ] `0.8578` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8570` — `o-nas.md`
  - [ ] `0.8539` — `index.md`
  - [ ] `0.8533` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8531` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8529` — `klauzula-informacyjna.md`

### Q09 [B] — `ile kosztuje renowacja dachu hali`

- **Expected:** `uslugi/renowacja-dachu.md`
- **Latency:** 19.3 ms
- **Top-K:**
  - [✓] `0.9115` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8999` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8991` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8916` — `uslugi.md`
  - [✓] `0.8910` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8904` — `404.md`
  - [✓] `0.8901` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8901` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8897` — `o-nas.md`
  - [✓] `0.8892` — `uslugi/renowacja-dachu.md`

### Q10 [B] — `zgodność z BHP i przepisami`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 19.6 ms
- **Top-K:**
  - [✓] `0.8766` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8653` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8619` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8595` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8507` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8479` — `index.md`
  - [✓] `0.8456` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8435` — `uslugi.md`
  - [✓] `0.8428` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8411` — `polityka-prywatnosci.md`

### Q11 [C] — `PN-EN 795`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 13.9 ms
- **Top-K:**
  - [✓] `0.8605` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8389` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8351` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8325` — `realizacje.md`
  - [✓] `0.8293` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8290` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8286` — `404.md`
  - [ ] `0.8286` — `index.md`
  - [ ] `0.8285` — `index.md`
  - [✓] `0.8284` — `uslugi/systemy-asekuracyjne.md`

### Q12 [C] — `+48 730 004 873`

- **Expected:** `kontakt.md`
- **Latency:** 19.1 ms
- **Top-K:**
  - [✓] `1.3800` — `kontakt.md`
  - [ ] `0.8564` — `polityka-prywatnosci.md`
  - [ ] `0.8546` — `realizacje.md`
  - [ ] `0.8545` — `index.md`
  - [ ] `0.8535` — `404.md`
  - [ ] `0.8528` — `polityka-prywatnosci.md`
  - [✓] `0.8527` — `kontakt.md`
  - [ ] `0.8521` — `polityka-prywatnosci.md`
  - [ ] `0.8517` — `o-nas.md`
  - [ ] `0.8515` — `klauzula-informacyjna.md`

### Q13 [C] — `PRO-Leak Control`

- **Expected:** `uslugi/serwis-membran-pvc.md`, `uslugi/systemy-asekuracyjne.md`
- **Latency:** 14.3 ms
- **Top-K:**
  - [✓] `0.8684` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8645` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8542` — `uslugi.md`
  - [✓] `0.8536` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8472` — `404.md`
  - [✓] `0.8428` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8414` — `uslugi.md`
  - [ ] `0.8394` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8376` — `uslugi.md`
  - [ ] `0.8356` — `index.md`

### Q14 [C] — `100 000 m²`

- **Expected:** `uslugi/serwis-membran-pvc.md`
- **Latency:** 14.3 ms
- **Top-K:**
  - [ ] `0.8420` — `realizacje.md`
  - [ ] `0.8413` — `o-nas.md`
  - [ ] `0.8391` — `realizacje.md`
  - [ ] `0.8387` — `uslugi.md`
  - [ ] `0.8357` — `uslugi.md`
  - [ ] `0.8350` — `o-nas.md`
  - [ ] `0.8339` — `kontakt.md`
  - [ ] `0.8329` — `uslugi.md`
  - [ ] `0.8305` — `404.md`
  - [ ] `0.8287` — `o-nas.md`

### Q15 [D] — `przepis na zupę pomidorową`

- **Expected:** _(nonsense — score only)_
- **Latency:** 15.3 ms
- **Top-K:**
  - [ ] `0.8251` — `klauzula-informacyjna.md`
  - [ ] `0.8182` — `polityka-prywatnosci.md`
  - [ ] `0.8176` — `polityka-prywatnosci.md`
  - [ ] `0.8155` — `404.md`
  - [ ] `0.8152` — `polityka-prywatnosci.md`
  - [ ] `0.8145` — `polityka-cookies.md`
  - [ ] `0.8142` — `polityka-cookies.md`
  - [ ] `0.8135` — `klauzula-informacyjna.md`
  - [ ] `0.8129` — `polityka-cookies.md`
  - [ ] `0.8124` — `polityka-prywatnosci.md`

### Q16 [D] — `jakie akcje kupić w 2026 roku`

- **Expected:** _(nonsense — score only)_
- **Latency:** 22.4 ms
- **Top-K:**
  - [ ] `0.8441` — `uslugi.md`
  - [ ] `0.8420` — `klauzula-informacyjna.md`
  - [ ] `0.8415` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8412` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8405` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8392` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8381` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8369` — `index.md`
  - [ ] `0.8363` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8352` — `uslugi/renowacja-dachu.md`

### Q17 [D] — `quantum entanglement explained`

- **Expected:** _(nonsense — score only)_
- **Latency:** 15.5 ms
- **Top-K:**
  - [ ] `0.7847` — `polityka-prywatnosci.md`
  - [ ] `0.7810` — `index.md`
  - [ ] `0.7802` — `klauzula-informacyjna.md`
  - [ ] `0.7782` — `index.md`
  - [ ] `0.7774` — `uslugi.md`
  - [ ] `0.7773` — `polityka-prywatnosci.md`
  - [ ] `0.7765` — `realizacje.md`
  - [ ] `0.7758` — `polityka-prywatnosci.md`
  - [ ] `0.7751` — `polityka-prywatnosci.md`
  - [ ] `0.7738` — `404.md`

### Q18 [E] — `dach`

- **Expected:** `index.md`, `uslugi.md`, `uslugi/renowacja-dachu.md`, `uslugi/termomodernizacja-dachu.md`, `uslugi/serwis-membran-pvc.md`, `uslugi/systemy-asekuracyjne.md`
- **Latency:** 9.7 ms
- **Top-K:**
  - [✓] `1.0412` — `index.md`
  - [ ] `1.0150` — `o-nas.md`
  - [✓] `1.0000` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.9362` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8444` — `index.md`
  - [ ] `0.8404` — `realizacje.md`
  - [✓] `0.8377` — `uslugi.md`
  - [ ] `0.8315` — `404.md`
  - [ ] `0.8306` — `o-nas.md`
  - [✓] `0.8291` — `uslugi/renowacja-dachu.md`
