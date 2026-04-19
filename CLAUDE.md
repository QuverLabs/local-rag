# Priorytety pracy w tym repo

- **Jakość retrievalu > wszystko inne.** Nie optymalizuj pod szybkość iteracji
  ani pod „mniej kodu" kosztem jakości wyników wyszukiwania. Jeśli zmiana
  poprawia trafność, nawet drobna, jest pożądana.
- **Re-ingest jest OK.** Nie unikaj zmian, które wymagają ponownego
  indeksowania bazy (zmiana chunkingu, prefiksów `passage:`/`query:`, modelu,
  rozszerzenia). Proponuj je wprost, jeśli uważasz że podnoszą jakość —
  koszt ~minuty re-ingestu jest akceptowalny.
