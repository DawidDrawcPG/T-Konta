# T-konta — program do nauki kont T

## Co można robić w wersji web

- dodać konto,
- zmienić nazwę konta,
- usunąć konto,
- dodać zapis Winien/Ma,
- poprawić zapis,
- usunąć zapis,
- podglądać sumy i saldo,
- korzystać z pulpitu wszystkich kont i osobnego widoku Winien/Ma,
- ustawić typ konta: aktywne, pasywne, aktywno-pasywne, kosztowe albo przychodowe,
- wskazać stronę salda początkowego (Wn/Ma),
- nadawać zapisom numery operacji, także z literami, np. `9`, `9a`, `9b`,
- dopisywać nowe pozycje pod wcześniej wprowadzonymi zapisami,
- wyszukiwać i filtrować konta,
- samodzielnie dopisywać pozycje operacji do wybranych kont, bez automatycznego doboru kont,
- sprawdzić dla każdego numeru operacji, czy suma Wn równa się sumie Ma,
- eksportować i importować całe ćwiczenie w XLSX,
- eksportować wszystkie konta do XLSX w prostym układzie arkusza `T-konto`:
  nazwa nad poziomą linią, kwoty po obu stronach osi pionowej oraz numery
  operacji `9a)` po stronie Wn i `(9a` po stronie Ma,
- rozróżniać po wpisaniu zapis zwiększający (zielony) od zmniejszającego
  (czerwony), zależnie od typu konta — w widoku aplikacji i w eksporcie XLSX.

Po starcie pulpit jest pusty. Student sam tworzy konta i wpisuje zapisy zgodnie
z treścią ćwiczenia.

**Dane działają w pamięci bieżącego uruchomienia, dlatego pracę należy zachować przez eksport XLSX, a później odtworzyć przez import.**

---

## Uruchomienie na iPadzie i innych tabletach

Najprostszy sposób uruchomienia T-kont na iPadzie, tablecie z Androidem albo innym urządzeniu mobilnym to **GitHub Codespaces**.

Nie trzeba instalować Pythona ani pobierać programu na tablet. Program uruchamia się na serwerze GitHub, a korzysta się z niego w przeglądarce.

### Co będzie potrzebne

- konto GitHub,
- połączenie z Internetem,
- przeglądarka internetowa, np. Safari, Chrome albo Edge.

### Krok 1 — otwórz repozytorium

1. Otwórz w przeglądarce:
   <https://github.com/DawidDrawcPG/T-Konta>
2. Zaloguj się na swoje konto GitHub.
3. Kliknij zielony przycisk **Code**.
4. Wybierz zakładkę **Codespaces**.
5. Kliknij **Create codespace on main**.

> Jeśli na iPadzie lub tablecie nie widać zakładki **Codespaces**, włącz w przeglądarce wersję strony dla komputera. W Safari użyj opcji **Poproś o witrynę na komputer**.

### Krok 2 — uruchom program

Po chwili otworzy się środowisko podobne do Visual Studio Code.

W dolnej części ekranu znajdź terminal i wpisz:

```text
python app.py
```

Następnie naciśnij **Enter**.

Po uruchomieniu powinien pojawić się komunikat:

```text
T-konta działają: http://localhost:8000
```

GitHub Codespaces wykryje port `8000` i umożliwi otwarcie programu w przeglądarce.

Jeżeli pojawi się komunikat o wykrytym porcie, wybierz **Open in Browser**.

### Krok 3 — korzystaj z T-kont

Po otwarciu programu pojawi się pusty pulpit.

Kliknij **Nowe konto T**, aby utworzyć konto potrzebne w ćwiczeniu. Możesz normalnie dodawać konta, zapisy Wn/Ma, sprawdzać operacje oraz importować i eksportować pliki XLSX.

Program działa w przeglądarce, więc można korzystać z niego na:

- iPadzie,
- tablecie z Androidem,
- telefonie,
- komputerze.

### Zapisanie pracy na tablecie

Przed zakończeniem pracy kliknij **Eksportuj do XLSX** i zapisz pobrany plik.

Po ponownym uruchomieniu Codespaces dane w T-kontach mogą być puste, ponieważ aplikacja przechowuje bieżący stan w pamięci uruchomionego programu.

Aby wrócić do wcześniejszego ćwiczenia:

1. uruchom ponownie T-konta,
2. kliknij **Importuj ćwiczenie XLSX**,
3. wybierz wcześniej zapisany plik.

### Ważne informacje o GitHub Codespaces

- Codespace może zostać automatycznie zatrzymany po okresie bezczynności.
- Po zatrzymaniu można go ponownie uruchomić z GitHub.
- GitHub może stosować miesięczne limity użycia Codespaces zależne od rodzaju konta i ustawień rozliczeń.
- Jeśli Codespaces pokazuje komunikat o limicie, budżecie albo problemie z płatnością, należy sprawdzić ustawienia **Settings → Billing and licensing** na koncie GitHub.

---

## Uruchomienie od zera — Windows 10 i Windows 11

Poniższa instrukcja jest dla osoby bez Pythona, Git-a, Visual Studio Code i doświadczenia technicznego. Wystarczy komputer z Windows, przeglądarka i około 5 minut.

### Co będzie potrzebne

- połączenie z Internetem — tylko do pierwszego pobrania programu i Pythona;
- przeglądarka, np. Chrome, Edge albo Firefox.

T-konta działają lokalnie na komputerze. Nie trzeba zakładać konta, instalować Excel-a ani pobierać dodatkowych bibliotek Pythona. Nie używa się też poleceń `pip install`.

### Krok 1 — pobierz program z GitHub

1. Otwórz <https://github.com/DawidDrawcPG/T-Konta>.
2. Kliknij zielony przycisk **Code**, a następnie **Download ZIP**.
3. Otwórz folder **Pobrane** i znajdź plik `T-Konta-main.zip`.
4. Kliknij go prawym przyciskiem myszy, wybierz **Wyodrębnij wszystko...**, a potem **Wyodrębnij**.
5. Powstanie folder `T-Konta-main`.

> **Nie uruchamiaj programu bezpośrednio z pliku ZIP. Najpierw zawsze go wypakuj.**

### Krok 2 — zainstaluj Python (tylko jeden raz)

1. Otwórz oficjalną stronę <https://www.python.org/downloads/windows/>.
2. Pobierz najnowszy **Python 3** dla Windows i uruchom instalator.
3. W pierwszym oknie instalatora zaznacz pole **Add python.exe to PATH**.
4. Kliknij **Install Now**, poczekaj na zakończenie instalacji i zamknij instalator.

To jedyna instalacja wymagana do pracy z programem.

### Krok 3 — uruchom T-konta

1. Otwórz wypakowany folder `T-Konta-main`.
2. Kliknij pasek adresu Eksploratora plików u góry okna, tam gdzie widać ścieżkę folderu.
3. Wpisz dokładnie `cmd` i naciśnij **Enter**.
4. Otworzy się czarne okno z białym tekstem. Wpisz w nim:

   ```text
   py app.py
   ```

5. Naciśnij **Enter**. Gdy pojawi się adres `http://localhost:8000`, program działa prawidłowo.
6. Nie zamykaj czarnego okna podczas pracy w T-kontach.
7. Otwórz przeglądarkę, wpisz w pasku adresu `http://localhost:8000` i naciśnij **Enter**.

Pojawi się pusty pulpit. Kliknij **Nowe konto T**, aby utworzyć konto potrzebne w ćwiczeniu. Student sam wpisuje nazwę, numer i rodzaj konta oraz zapisy Wn i Ma.

### Zapisanie pracy i zamknięcie programu

1. Kliknij w programie **Eksportuj do XLSX**.
2. Przeglądarka pobierze plik z ćwiczeniem. Zapamiętaj, gdzie został zapisany.
3. Wróć do czarnego okna i naciśnij jednocześnie **Ctrl + C**.
4. Zamknij czarne okno i przeglądarkę.

Przy kolejnym uruchomieniu pulpit będzie pusty. Aby kontynuować pracę, uruchom program ponownie, kliknij **Importuj ćwiczenie XLSX** i wybierz wcześniej wyeksportowany plik.

### Najczęstsze problemy

| Co widzę? | Co zrobić? |
| --- | --- |
| `py` nie jest rozpoznawany | Python nie został zainstalowany albo podczas instalacji nie zaznaczono **Add python.exe to PATH**. Zainstaluj go ponownie, zaznacz to pole i otwórz nowe czarne okno. |
| Nie ma pliku `app.py` | Czarne okno jest otwarte w złym folderze. Zamknij je, wejdź do folderu `T-Konta-main`, wpisz `cmd` w jego pasku adresu i spróbuj ponownie. |
| `localhost:8000` się nie otwiera | Sprawdź, czy czarne okno z poleceniem `py app.py` nadal jest otwarte. Jeśli je zamknięto, uruchom program ponownie. |
| Port 8000 jest zajęty | Zamknij inne okno T-kont. Jeśli problem zostanie, wpisz `py app.py 8001`, a w przeglądarce otwórz `http://localhost:8001`. |
| Po ponownym uruchomieniu nie ma kont | To oczekiwane: dane są przechowywane tylko podczas bieżącej pracy. Przed zamknięciem użyj **Eksportuj do XLSX**, a po starcie **Importuj ćwiczenie XLSX**. |

### Aktualizacja programu

Pobierz nowy ZIP ze strony GitHub, wypakuj go do nowego folderu i uruchom według tej samej instrukcji. Plik XLSX wyeksportowany ze starszej wersji można następnie zaimportować do nowej wersji.

## Twórca

Dawid Drawc
