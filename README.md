# Parcia i odpory — Pantelidis (2019)

Lokalny prototyp (Streamlit) do udostępniania obliczeń parć/odporów granicznych
oraz przemieszczeń granicznych ściany gładkiej według wzorów Pantelidisa.

## Uruchomienie

```bash
cd /home/janusz/Dokumenty/ksiazka_JK_MW/SCIANA/parcia_pantelidis
pip install -r requirements.txt
streamlit run app.py
```

Testy:

```bash
pytest -v
```

## Zakres (v0)

- \(K_{oe}\), \(K_{ae}\), \(K_{pe}\) i \(\sigma_o,\sigma_a,\sigma_p\) (homogeniczna warstwa)
- opcjonalnie \(k_h\), \(k_v\)
- obciążenie naziomu przez \(z_\mathrm{eff}\)
- \(\Delta x_{a;\lim}\), \(\Delta x_{p;\lim}\) oraz moduły dwuliniowe \(E_{a/p;\mathrm{bilinear}}\) (ściana gładka)
- przykład: \(\gamma=21\), \(c'=30\,\mathrm{kPa}\), \(\varphi'=17{,}5^\circ\)

## Literatura

1. Kozubal, J. W., Wyjadłowski, M. (2025). *Poradnik geotechniki*. Wrocław: Dolnośląskie Wydawnictwo Edukacyjne. ISBN 978-83-7125-308-9.
2. Pantelidis, L. (2019). The Generalized Coefficients of Earth Pressure: A Unified Approach. *Applied Sciences*, 9(24), 5291. https://doi.org/10.3390/app9245291
