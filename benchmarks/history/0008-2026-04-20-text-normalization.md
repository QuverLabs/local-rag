# Benchmark 0008 — text-normalization

- **Run date:** 2026-04-20 20:11:34
- **Commit:** `f4a6741908c09238cde17cf31a9ba465fddabe55` _(worktree dirty)_
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
| A | 6 | 67% | 100% | 0.833 | 0.9076 |
| B | 4 | 75% | 100% | 0.875 | 0.8827 |
| C | 4 | 100% | 100% | 1.000 | 0.9132 |
| D | 3 | 0% | 0% | 0.000 | 0.8167 |
| E | 1 | 100% | 100% | 1.000 | 1.0000 |

**Discrimination gap (A vs. D, avg top-1):** `+0.0909`  
_Higher is better — it means nonsense queries score noticeably lower than on-topic ones, letting a threshold filter them._

## Per-query detail

### Q01 [A] — `renowacja dachu bez zrywania starego pokrycia`

- **Expected:** `uslugi/renowacja-dachu.md`
- **Latency:** 65.7 ms
- **Top-K:**
  - [✓] `0.9555` — `uslugi/renowacja-dachu.md`
  - [ ] `0.9030` — `o-nas.md`
  - [ ] `0.8932` — `uslugi.md`
  - [✓] `0.8890` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8888` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8879` — `o-nas.md`
  - [✓] `0.8874` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8166` — `index.md`
  - [✓] `0.7006` — `uslugi/renowacja-dachu.md`

### Q02 [A] — `detekcja przecieków na dachu z membraną`

- **Expected:** `uslugi/serwis-membran-pvc.md`
- **Latency:** 26.0 ms
- **Top-K:**
  - [ ] `0.9039` — `404.md`
  - [✓] `0.8979` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8962` — `realizacje.md`
  - [✓] `0.8961` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8923` — `uslugi.md`
  - [✓] `0.8899` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8892` — `realizacje.md`
  - [ ] `0.8850` — `index.md`
  - [ ] `0.8835` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8831` — `uslugi/renowacja-dachu.md`

### Q03 [A] — `linia życia i punkty kotwiczenia na dachu hali`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 28.1 ms
- **Top-K:**
  - [✓] `0.9003` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8943` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8865` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8804` — `realizacje.md`
  - [ ] `0.8786` — `uslugi.md`
  - [ ] `0.8783` — `404.md`
  - [✓] `0.8779` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8768` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8760` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8756` — `uslugi/systemy-asekuracyjne.md`

### Q04 [A] — `termomodernizacja dachu przemysłowego`

- **Expected:** `uslugi/termomodernizacja-dachu.md`
- **Latency:** 21.0 ms
- **Top-K:**
  - [✓] `0.9088` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8927` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8907` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8899` — `uslugi.md`
  - [✓] `0.8882` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8864` — `index.md`
  - [ ] `0.8854` — `o-nas.md`
  - [ ] `0.8849` — `index.md`
  - [ ] `0.8843` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8809` — `uslugi.md`

### Q05 [A] — `adres biura i telefon kontaktowy`

- **Expected:** `kontakt.md`
- **Latency:** 16.7 ms
- **Top-K:**
  - [ ] `0.8775` — `polityka-prywatnosci.md`
  - [✓] `0.8763` — `kontakt.md`
  - [ ] `0.8731` — `polityka-prywatnosci.md`
  - [ ] `0.8729` — `polityka-prywatnosci.md`
  - [ ] `0.8681` — `polityka-prywatnosci.md`
  - [ ] `0.8675` — `polityka-prywatnosci.md`
  - [✓] `0.8652` — `kontakt.md`
  - [ ] `0.8631` — `klauzula-informacyjna.md`
  - [ ] `0.8585` — `index.md`
  - [ ] `0.8565` — `klauzula-informacyjna.md`

### Q06 [A] — `polityka prywatności RODO`

- **Expected:** `polityka-prywatnosci.md`, `klauzula-informacyjna.md`
- **Latency:** 19.8 ms
- **Top-K:**
  - [✓] `0.8997` — `polityka-prywatnosci.md`
  - [✓] `0.8942` — `polityka-prywatnosci.md`
  - [✓] `0.8908` — `klauzula-informacyjna.md`
  - [✓] `0.8872` — `klauzula-informacyjna.md`
  - [✓] `0.8850` — `polityka-prywatnosci.md`
  - [✓] `0.8850` — `polityka-prywatnosci.md`
  - [✓] `0.8829` — `klauzula-informacyjna.md`
  - [✓] `0.8817` — `polityka-prywatnosci.md`
  - [✓] `0.8762` — `polityka-prywatnosci.md`
  - [ ] `0.8741` — `polityka-cookies.md`

### Q07 [B] — `gwarancja szczelności 20 lat`

- **Expected:** `uslugi/renowacja-dachu.md`, `index.md`, `uslugi.md`
- **Latency:** 18.6 ms
- **Top-K:**
  - [✓] `0.8741` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8672` — `index.md`
  - [✓] `0.8666` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8664` — `404.md`
  - [ ] `0.8645` — `o-nas.md`
  - [✓] `0.8644` — `index.md`
  - [ ] `0.8633` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8631` — `index.md`
  - [ ] `0.8629` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8626` — `uslugi.md`

### Q08 [B] — `dla jakich obiektów pracujecie`

- **Expected:** `o-nas.md`, `uslugi.md`
- **Latency:** 14.7 ms
- **Top-K:**
  - [ ] `0.8688` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8636` — `uslugi.md`
  - [✓] `0.8617` — `uslugi.md`
  - [ ] `0.8593` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8578` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8542` — `o-nas.md`
  - [ ] `0.8539` — `index.md`
  - [ ] `0.8535` — `polityka-prywatnosci.md`
  - [ ] `0.8533` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8531` — `uslugi/systemy-asekuracyjne.md`

### Q09 [B] — `ile kosztuje renowacja dachu hali`

- **Expected:** `uslugi/renowacja-dachu.md`
- **Latency:** 19.6 ms
- **Top-K:**
  - [✓] `0.9115` — `uslugi/renowacja-dachu.md`
  - [✓] `0.8999` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8991` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8914` — `uslugi/termomodernizacja-dachu.md`
  - [✓] `0.8910` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8903` — `o-nas.md`
  - [ ] `0.8899` — `realizacje.md`
  - [✓] `0.8892` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8890` — `404.md`
  - [ ] `0.8879` — `uslugi.md`

### Q10 [B] — `zgodność z BHP i przepisami`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 20.0 ms
- **Top-K:**
  - [✓] `0.8766` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8653` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8619` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8568` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8507` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8480` — `uslugi.md`
  - [ ] `0.8479` — `index.md`
  - [✓] `0.8456` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8441` — `polityka-prywatnosci.md`
  - [✓] `0.8428` — `uslugi/systemy-asekuracyjne.md`

### Q11 [C] — `PN-EN 795`

- **Expected:** `uslugi/systemy-asekuracyjne.md`
- **Latency:** 14.7 ms
- **Top-K:**
  - [✓] `0.8605` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8389` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8338` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8314` — `realizacje.md`
  - [ ] `0.8308` — `uslugi.md`
  - [ ] `0.8296` — `realizacje.md`
  - [✓] `0.8293` — `uslugi/systemy-asekuracyjne.md`
  - [✓] `0.8290` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8286` — `404.md`
  - [ ] `0.8286` — `index.md`

### Q12 [C] — `+48 730 004 873`

- **Expected:** `kontakt.md`
- **Latency:** 15.0 ms
- **Top-K:**
  - [✓] `0.9237` — `kontakt.md`
  - [ ] `0.8322` — `polityka-prywatnosci.md`
  - [ ] `0.8313` — `polityka-prywatnosci.md`
  - [ ] `0.8309` — `polityka-prywatnosci.md`
  - [ ] `0.8262` — `polityka-prywatnosci.md`
  - [ ] `0.8240` — `klauzula-informacyjna.md`
  - [ ] `0.8235` — `klauzula-informacyjna.md`
  - [ ] `0.8230` — `polityka-prywatnosci.md`
  - [ ] `0.8217` — `polityka-prywatnosci.md`
  - [ ] `0.8212` — `klauzula-informacyjna.md`

### Q13 [C] — `PRO-Leak Control`

- **Expected:** `uslugi/serwis-membran-pvc.md`, `uslugi/systemy-asekuracyjne.md`
- **Latency:** 16.0 ms
- **Top-K:**
  - [✓] `0.8684` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8645` — `uslugi/serwis-membran-pvc.md`
  - [✓] `0.8538` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8530` — `uslugi.md`
  - [ ] `0.8476` — `404.md`
  - [✓] `0.8428` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8383` — `uslugi.md`
  - [ ] `0.8376` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8357` — `uslugi.md`
  - [ ] `0.8356` — `index.md`

### Q14 [C] — `100 000 m²`

- **Expected:** `uslugi/serwis-membran-pvc.md`
- **Latency:** 13.1 ms
- **Top-K:**
  - [✓] `1.0000` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8391` — `realizacje.md`
  - [ ] `0.8384` — `uslugi.md`
  - [ ] `0.8371` — `o-nas.md`
  - [ ] `0.8353` — `o-nas.md`
  - [ ] `0.8353` — `realizacje.md`
  - [ ] `0.8340` — `uslugi.md`
  - [ ] `0.8314` — `uslugi.md`
  - [ ] `0.8312` — `kontakt.md`
  - [ ] `0.8308` — `404.md`

### Q15 [D] — `przepis na zupę pomidorową`

- **Expected:** _(nonsense — score only)_
- **Latency:** 15.5 ms
- **Top-K:**
  - [ ] `0.8251` — `klauzula-informacyjna.md`
  - [ ] `0.8217` — `polityka-prywatnosci.md`
  - [ ] `0.8142` — `404.md`
  - [ ] `0.8142` — `polityka-cookies.md`
  - [ ] `0.8140` — `polityka-prywatnosci.md`
  - [ ] `0.8137` — `polityka-cookies.md`
  - [ ] `0.8135` — `klauzula-informacyjna.md`
  - [ ] `0.8130` — `polityka-prywatnosci.md`
  - [ ] `0.8129` — `polityka-cookies.md`
  - [ ] `0.8124` — `polityka-prywatnosci.md`

### Q16 [D] — `jakie akcje kupić w 2026 roku`

- **Expected:** _(nonsense — score only)_
- **Latency:** 21.2 ms
- **Top-K:**
  - [ ] `0.8420` — `klauzula-informacyjna.md`
  - [ ] `0.8415` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8412` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8406` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8392` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8388` — `uslugi.md`
  - [ ] `0.8381` — `uslugi/systemy-asekuracyjne.md`
  - [ ] `0.8369` — `index.md`
  - [ ] `0.8363` — `uslugi/termomodernizacja-dachu.md`
  - [ ] `0.8352` — `uslugi/renowacja-dachu.md`

### Q17 [D] — `quantum entanglement explained`

- **Expected:** _(nonsense — score only)_
- **Latency:** 14.8 ms
- **Top-K:**
  - [ ] `0.7830` — `polityka-prywatnosci.md`
  - [ ] `0.7819` — `klauzula-informacyjna.md`
  - [ ] `0.7810` — `index.md`
  - [ ] `0.7782` — `index.md`
  - [ ] `0.7767` — `polityka-prywatnosci.md`
  - [ ] `0.7767` — `uslugi.md`
  - [ ] `0.7766` — `polityka-prywatnosci.md`
  - [ ] `0.7764` — `polityka-prywatnosci.md`
  - [ ] `0.7743` — `uslugi.md`
  - [ ] `0.7733` — `klauzula-informacyjna.md`

### Q18 [E] — `dach`

- **Expected:** `index.md`, `uslugi.md`, `uslugi/renowacja-dachu.md`, `uslugi/termomodernizacja-dachu.md`, `uslugi/serwis-membran-pvc.md`, `uslugi/systemy-asekuracyjne.md`
- **Latency:** 10.8 ms
- **Top-K:**
  - [✓] `1.0000` — `uslugi/serwis-membran-pvc.md`
  - [ ] `0.8395` — `realizacje.md`
  - [✓] `0.8380` — `uslugi.md`
  - [ ] `0.8306` — `404.md`
  - [✓] `0.8301` — `uslugi.md`
  - [ ] `0.8294` — `o-nas.md`
  - [✓] `0.8291` — `uslugi/renowacja-dachu.md`
  - [ ] `0.8274` — `o-nas.md`
