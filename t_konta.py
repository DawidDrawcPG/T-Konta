#!/usr/bin/env python3
"""Silnik ćwiczeń z księgowania na kontach T."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
import re


# Rodzaj konta opisuje jego zachowanie na T-koncie, a nie konkretny numer
# z jednego zakładowego planu kont.  Dzięki temu student może samodzielnie
# tworzyć np. 490, 640 czy konta zespołów 5, 7 i 8 zgodnie z treścią zadania.
TYPY_KONT = {
    "Aktywne", "Pasywne", "Aktywno-pasywne", "Kosztowe",
    "Kosztowe kalkulacyjne", "Przychodowe", "Techniczne / rozliczeniowe",
    "Wynik finansowy",
}
NORMALNA_STRONA = {
    "Aktywne": "W", "Pasywne": "M", "Kosztowe": "W",
    "Kosztowe kalkulacyjne": "W", "Przychodowe": "M",
}


@dataclass
class Zapis:
    id: int
    numer_operacji: str
    strona: str
    kwota: Decimal
    data: str
    opis: str


@dataclass
class KontoT:
    id: int
    nazwa: str
    numer: str
    typ: str = "Aktywne"
    saldo_poczatkowe: Decimal = Decimal("0.00")
    strona_salda_poczatkowego: str = "W"
    aktywne: bool = True
    zamkniete: bool = False
    zapisy: list[Zapis] = field(default_factory=list)

    @property
    def normalna_strona(self) -> str | None:
        # Konto aktywno-pasywne nie ma jednej ustawowej strony "zawsze".
        # W ćwiczeniu użytkownik wybiera stronę typową danego konta; na jej
        # podstawie kolor oznacza zwiększenie (zielony) lub zmniejszenie (czerwony).
        if self.typ == "Wynik finansowy":
            return None
        return NORMALNA_STRONA.get(self.typ) or self.strona_salda_poczatkowego

    def ton_zapisu(self, strona: str) -> str:
        """Efekt zapisu jest pokazywany po wpisaniu go przez studenta."""
        if self.normalna_strona is None:
            return "neutralny"
        return "zwiekszenie" if strona == self.normalna_strona else "zmniejszenie"

    def dodaj_zapis(self, zapis_id: int, numer_operacji: str, strona: str, kwota: Decimal, data_zapisu: str, opis: str) -> Zapis:
        numer_operacji = self.normalizuj_numer_operacji(numer_operacji)
        self._waliduj_zapis(numer_operacji, strona, kwota, data_zapisu)
        zapis = Zapis(zapis_id, numer_operacji, strona, kwota.quantize(Decimal("0.01")), data_zapisu, opis.strip())
        self.zapisy.append(zapis)
        return zapis

    @staticmethod
    def normalizuj_numer_operacji(numer_operacji: str) -> str:
        numer = numer_operacji.strip()
        return numer.upper() if re.fullmatch(r"[ivxlcdm]+", numer, flags=re.IGNORECASE) else numer.lower()

    @staticmethod
    def _waliduj_zapis(numer_operacji: str, strona: str, kwota: Decimal, data_zapisu: str) -> None:
        if not re.fullmatch(r"(?:[1-9]\d*[a-z]*|[IVXLCDM]+)", numer_operacji):
            raise ValueError("Numer operacji musi mieć postać np. 9, 9a, 9b albo I, II, III.")
        if strona not in {"W", "M"}:
            raise ValueError("Strona musi być 'W' (Winien) lub 'M' (Ma).")
        if kwota <= 0:
            raise ValueError("Kwota musi być dodatnia.")
        try:
            date.fromisoformat(data_zapisu)
        except ValueError as exc:
            raise ValueError("Data musi mieć format RRRR-MM-DD.") from exc

    def pobierz_zapis(self, zapis_id: int) -> Zapis:
        for zapis in self.zapisy:
            if zapis.id == zapis_id:
                return zapis
        raise KeyError("Nie znaleziono zapisu.")

    def edytuj_zapis(self, zapis_id: int, numer_operacji: str, strona: str, kwota: Decimal, data_zapisu: str, opis: str) -> Zapis:
        zapis = self.pobierz_zapis(zapis_id)
        numer_operacji = self.normalizuj_numer_operacji(numer_operacji)
        self._waliduj_zapis(numer_operacji, strona, kwota, data_zapisu)
        zapis.numer_operacji, zapis.strona = numer_operacji, strona
        zapis.kwota, zapis.data, zapis.opis = kwota.quantize(Decimal("0.01")), data_zapisu, opis.strip()
        return zapis

    def usun_zapis(self, zapis_id: int) -> None:
        self.pobierz_zapis(zapis_id)
        self.zapisy = [z for z in self.zapisy if z.id != zapis_id]

    @property
    def suma_winien(self) -> Decimal:
        return sum((z.kwota for z in self.zapisy if z.strona == "W"), start=Decimal("0"))

    @property
    def suma_ma(self) -> Decimal:
        return sum((z.kwota for z in self.zapisy if z.strona == "M"), start=Decimal("0"))

    @property
    def saldo_netto(self) -> Decimal:
        sp = self.saldo_poczatkowe if self.strona_salda_poczatkowego == "W" else -self.saldo_poczatkowe
        return sp + self.suma_winien - self.suma_ma

    @property
    def saldo(self) -> Decimal:
        return self.saldo_netto

    @property
    def strona_salda(self) -> str | None:
        return "W" if self.saldo_netto > 0 else "M" if self.saldo_netto < 0 else None

    @property
    def ton_salda(self) -> str:
        if not self.strona_salda:
            return "neutralny"
        if self.normalna_strona is None:
            return "neutralny"
        return "zwiekszenie" if self.strona_salda == self.normalna_strona else "zmniejszenie"

    def as_dict(self) -> dict:
        return {
            "id": self.id, "nazwa": self.nazwa, "numer": self.numer, "typ": self.typ,
            "saldo_poczatkowe": f"{self.saldo_poczatkowe:.2f}",
            "strona_salda_poczatkowego": self.strona_salda_poczatkowego, "aktywne": self.aktywne, "zamkniete": self.zamkniete,
            "zapisy": [
                {"id": z.id, "numer_operacji": z.numer_operacji, "strona": z.strona, "kwota": f"{z.kwota:.2f}", "data": z.data, "opis": z.opis}
                for z in sorted(self.zapisy, key=lambda item: item.id)
            ],
            "suma_winien": f"{self.suma_winien:.2f}", "suma_ma": f"{self.suma_ma:.2f}",
            "saldo": f"{self.saldo:.2f}", "strona_salda": self.strona_salda, "ton_salda": self.ton_salda,
        }


class SilnikKont:
    DOZWOLONE_TYPY = TYPY_KONT

    def __init__(self) -> None:
        self.konta: list[KontoT] = []
        self._next_konto_id = 1
        self._next_zapis_id = 1

    @staticmethod
    def parse_kwota(raw: str, *, allow_zero: bool = False) -> Decimal:
        try:
            value = Decimal(str(raw).strip().replace(" ", "").replace(",", "."))
        except (InvalidOperation, AttributeError) as exc:
            raise ValueError("Niepoprawna kwota.") from exc
        if value < 0 or (value == 0 and not allow_zero):
            raise ValueError("Kwota musi być dodatnia." if not allow_zero else "Kwota nie może być ujemna.")
        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _strona_sp(typ: str, strona: str | None) -> str:
        normalna = NORMALNA_STRONA.get(typ)
        wybrana = (strona or normalna or "W").upper()
        if wybrana not in {"W", "M"}:
            raise ValueError("Strona salda początkowego musi być Wn albo Ma.")
        if normalna and wybrana != normalna:
            raise ValueError(f"Konto {typ.lower()} ma saldo początkowe po stronie {'Wn' if normalna == 'W' else 'Ma'}.")
        return wybrana

    @staticmethod
    def _waliduj_saldo_wynikowe(typ: str, saldo: Decimal) -> None:
        if typ in {"Kosztowe", "Kosztowe kalkulacyjne", "Przychodowe", "Wynik finansowy"} and saldo != 0:
            raise ValueError("Konta wynikowe w ćwiczeniu rozpoczynają się od salda 0,00.")

    def pobierz_konto(self, konto_id: int) -> KontoT:
        for konto in self.konta:
            if konto.id == konto_id:
                return konto
        raise KeyError("Nie znaleziono konta.")

    def dodaj_konto(self, nazwa: str, numer: str = "", typ: str = "Aktywne", saldo_poczatkowe: str = "0", strona_salda_poczatkowego: str | None = None, aktywne: bool = True) -> KontoT:
        nazwa, numer = nazwa.strip(), numer.strip() or str(self._next_konto_id)
        if not nazwa:
            raise ValueError("Nazwa konta nie może być pusta.")
        if any(k.numer == numer for k in self.konta):
            raise ValueError("Konto o tym numerze już istnieje.")
        if typ not in self.DOZWOLONE_TYPY:
            raise ValueError("Niepoprawny typ konta.")
        saldo = self.parse_kwota(saldo_poczatkowe, allow_zero=True)
        self._waliduj_saldo_wynikowe(typ, saldo)
        konto = KontoT(self._next_konto_id, nazwa, numer, typ, saldo, self._strona_sp(typ, strona_salda_poczatkowego), bool(aktywne))
        self._next_konto_id += 1
        self.konta.append(konto)
        return konto

    def zmien_dane_konta(self, konto_id: int, dane: dict) -> KontoT:
        konto = self.pobierz_konto(konto_id)
        nazwa, numer, typ = str(dane.get("name", konto.nazwa)).strip(), str(dane.get("number", konto.numer)).strip(), str(dane.get("type", konto.typ))
        if not nazwa or not numer:
            raise ValueError("Nazwa i numer konta nie mogą być puste.")
        if any(k.id != konto_id and k.numer == numer for k in self.konta):
            raise ValueError("Konto o tym numerze już istnieje.")
        if typ not in self.DOZWOLONE_TYPY:
            raise ValueError("Niepoprawny typ konta.")
        saldo = self.parse_kwota(dane.get("openingBalance", str(konto.saldo_poczatkowe)), allow_zero=True)
        self._waliduj_saldo_wynikowe(typ, saldo)
        strona_sp = self._strona_sp(typ, str(dane.get("openingSide", konto.strona_salda_poczatkowego)))
        konto.nazwa, konto.numer, konto.typ = nazwa, numer, typ
        konto.saldo_poczatkowe, konto.strona_salda_poczatkowego = saldo, strona_sp
        konto.aktywne = bool(dane.get("active", konto.aktywne))
        return konto

    def usun_konto(self, konto_id: int) -> None:
        self.pobierz_konto(konto_id)
        self.konta = [k for k in self.konta if k.id != konto_id]

    def wyczysc_konta(self) -> None:
        """Usuwa wszystkie konta oraz zapisy bieżącego ćwiczenia."""
        self.konta = []
        self._next_konto_id = 1
        self._next_zapis_id = 1

    def dodaj_zapis(self, konto_id: int, numer_operacji: str, strona: str, kwota_raw: str, data_zapisu: str, opis: str) -> Zapis:
        konto = self.pobierz_konto(konto_id)
        zapis = konto.dodaj_zapis(self._next_zapis_id, numer_operacji, strona, self.parse_kwota(kwota_raw), data_zapisu, opis)
        self._next_zapis_id += 1
        return zapis

    def edytuj_zapis(self, konto_id: int, zapis_id: int, numer_operacji: str, strona: str, kwota_raw: str, data_zapisu: str, opis: str) -> Zapis:
        konto = self.pobierz_konto(konto_id)
        return konto.edytuj_zapis(zapis_id, numer_operacji, strona, self.parse_kwota(kwota_raw), data_zapisu, opis)

    def usun_zapis(self, konto_id: int, zapis_id: int) -> None:
        konto = self.pobierz_konto(konto_id)
        konto.usun_zapis(zapis_id)

    @staticmethod
    def _sort_operacji(numer: str) -> tuple[int, str]:
        match = re.fullmatch(r"(\d+)([a-z]*)", numer)
        if match:
            return int(match.group(1)), match.group(2)
        rzymskie = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        if re.fullmatch(r"[IVXLCDM]+", numer):
            wartosc, poprzednia = 0, 0
            for znak in reversed(numer):
                biezaca = rzymskie[znak]
                wartosc += -biezaca if biezaca < poprzednia else biezaca
                poprzednia = max(poprzednia, biezaca)
            return 10**9 + wartosc, numer
        return 10**9 + 10**6, numer

    def operacje(self) -> list[dict]:
        grupy: dict[str, dict] = {}
        for konto in self.konta:
            for zapis in konto.zapisy:
                grupa = grupy.setdefault(zapis.numer_operacji, {"numer": zapis.numer_operacji, "wn": Decimal("0"), "ma": Decimal("0"), "pozycje": 0})
                grupa["wn" if zapis.strona == "W" else "ma"] += zapis.kwota
                grupa["pozycje"] += 1
        wynik = []
        for grupa in grupy.values():
            roznica = grupa["wn"] - grupa["ma"]
            zgodna = bool(grupa["wn"] and grupa["ma"] and roznica == 0)
            wynik.append({
                "numer": grupa["numer"], "suma_wn": f"{grupa['wn']:.2f}", "suma_ma": f"{grupa['ma']:.2f}",
                "roznica": f"{abs(roznica):.2f}", "brakujaca_strona": None if zgodna else "Ma" if roznica > 0 else "Wn" if roznica < 0 else "Wn i Ma",
                "status": "zgodna" if zgodna else "niezgodna", "pozycje": grupa["pozycje"],
            })
        return sorted(wynik, key=lambda item: self._sort_operacji(item["numer"]))

    def statusy_zamkniecia(self) -> dict[int, dict]:
        """Sprawdza ręczne przeksięgowania kont wynikowych na konto 860.

        Nie tworzy żadnego zapisu. Konto jest zamknięte tylko, gdy student
        sam wyzerował je zapisem o tej samej operacji i kwocie na koncie 860.
        """
        konto_860 = next((k for k in self.konta if k.numer == "860" and k.typ == "Wynik finansowy"), None)
        statusy: dict[int, dict] = {}
        for konto in self.konta:
            konto.zamkniete = False
            if konto.typ not in {"Kosztowe", "Przychodowe"}:
                continue
            if konto_860 is None:
                statusy[konto.id] = {"status": "brak_860", "opis": "Dodaj konto 860 „Wynik finansowy”, a następnie wprowadź własny zapis zamykający."}
                continue
            strona_zamkniecia = "M" if konto.typ == "Kosztowe" else "W"
            strona_860 = "W" if konto.typ == "Kosztowe" else "M"
            operacje_zamykajace = []
            for zapis in konto.zapisy:
                if zapis.strona != strona_zamkniecia:
                    continue
                if any(z860.numer_operacji == zapis.numer_operacji and z860.strona == strona_860 and z860.kwota == zapis.kwota for z860 in konto_860.zapisy):
                    operacje_zamykajace.append(zapis.numer_operacji)
            if konto.saldo_netto == 0 and operacje_zamykajace:
                konto.zamkniete = True
                statusy[konto.id] = {"status": "zamkniete", "opis": f"Zamknięte ręcznym przeksięgowaniem na konto 860 (operacja {', '.join(sorted(set(operacje_zamykajace), key=self._sort_operacji))})."}
            else:
                statusy[konto.id] = {"status": "do_zamkniecia", "opis": "Wprowadź ręczny zapis zamykający w korespondencji z kontem 860; po obu stronach operacji kwoty muszą się zgadzać."}
        return statusy

    def wczytaj_stan(self, dane: dict) -> None:
        konta = dane.get("konta")
        if not isinstance(konta, list):
            raise ValueError("Plik nie zawiera listy kont Kontownika.")
        nowy = SilnikKont()
        for konto in konta:
            utworzone = nowy.dodaj_konto(
                str(konto.get("nazwa", "")), str(konto.get("numer", "")), str(konto.get("typ", "Aktywne")),
                str(konto.get("saldo_poczatkowe", "0")), str(konto.get("strona_salda_poczatkowego", "W")), bool(konto.get("aktywne", True)),
            )
            for zapis in konto.get("zapisy", []):
                nowy.dodaj_zapis(utworzone.id, str(zapis.get("numer_operacji", "")), str(zapis.get("strona", "")), str(zapis.get("kwota", "")), str(zapis.get("data", date.today().isoformat())), str(zapis.get("opis", "")))
        self.konta, self._next_konto_id, self._next_zapis_id = nowy.konta, nowy._next_konto_id, nowy._next_zapis_id

    def as_dict(self) -> dict:
        statusy = self.statusy_zamkniecia()
        konta = []
        for konto in self.konta:
            dane = konto.as_dict()
            if konto.id in statusy:
                dane["zamkniecie"] = statusy[konto.id]
            konta.append(dane)
        return {"konta": konta, "operacje": self.operacje()}
