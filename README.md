# Program do T-kont

Teraz aplikacja działa w modelu:

- `index.html` — frontend (formularz i widok),
- `app.py` + `t_konta.py` — backend i silnik logiki w Pythonie.

## Co można robić w wersji web

- dodać konto,
- zmienić nazwę konta,
- usunąć konto,
- dodać zapis Winien/Ma,
- poprawić zapis,
- usunąć zapis,
- podglądać sumy i saldo.

## Jak odpalić na localhost (krok po kroku)

1. Przejdź do katalogu projektu:

```bash
cd /workspace/T-Konta
```

2. Uruchom serwer backendu:

```bash
python3 app.py
```

3. Otwórz stronę w przeglądarce:

```text
http://localhost:8000
```

4. Zatrzymanie serwera: w terminalu naciśnij `Ctrl + C`.

### Szybka diagnostyka

- Jeśli port `8000` jest zajęty, zamknij inny proces na tym porcie i uruchom ponownie `python3 app.py`.
- Jeśli strona się nie ładuje, sprawdź czy w terminalu po starcie serwera nie ma błędów.

## Wersja CLI

Nadal dostępna:

```bash
python3 t_konta.py
```
## Gałąź domyślna

Pracujemy domyślnie na gałęzi `main`. Nową gałąź twórz tylko wtedy, gdy jest to potrzebne.

