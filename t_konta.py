#!/usr/bin/env python3
"""Silnik T-kont + opcjonalne CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


@dataclass
class Zapis:
    id: int
    strona: str
    kwota: Decimal


@dataclass
class KontoT:
    id: int
    nazwa: str
    zapisy: list[Zapis] = field(default_factory=list)

    def dodaj_zapis(self, zapis_id: int, strona: str, kwota: Decimal) -> Zapis:
        if strona not in {"W", "M"}:
            raise ValueError("Strona musi być 'W' (Winien) lub 'M' (Ma).")
        if kwota <= 0:
            raise ValueError("Kwota musi być dodatnia.")
        zapis = Zapis(id=zapis_id, strona=strona, kwota=kwota.quantize(Decimal("0.01")))
        self.zapisy.append(zapis)
        return zapis

    def pobierz_zapis(self, zapis_id: int) -> Zapis:
        for zapis in self.zapisy:
            if zapis.id == zapis_id:
                return zapis
        raise KeyError("Nie znaleziono zapisu.")

    def edytuj_zapis(self, zapis_id: int, strona: str, kwota: Decimal) -> Zapis:
        zapis = self.pobierz_zapis(zapis_id)
        if strona not in {"W", "M"}:
            raise ValueError("Strona musi być 'W' (Winien) lub 'M' (Ma).")
        if kwota <= 0:
            raise ValueError("Kwota musi być dodatnia.")
        zapis.strona = strona
        zapis.kwota = kwota.quantize(Decimal("0.01"))
        return zapis

    def usun_zapis(self, zapis_id: int) -> None:
        self.zapisy = [z for z in self.zapisy if z.id != zapis_id]

    @property
    def suma_winien(self) -> Decimal:
        return sum((z.kwota for z in self.zapisy if z.strona == "W"), start=Decimal("0"))

    @property
    def suma_ma(self) -> Decimal:
        return sum((z.kwota for z in self.zapisy if z.strona == "M"), start=Decimal("0"))

    @property
    def saldo(self) -> Decimal:
        return self.suma_winien - self.suma_ma

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "nazwa": self.nazwa,
            "zapisy": [
                {"id": z.id, "strona": z.strona, "kwota": f"{z.kwota:.2f}"}
                for z in self.zapisy
            ],
            "suma_winien": f"{self.suma_winien:.2f}",
            "suma_ma": f"{self.suma_ma:.2f}",
            "saldo": f"{self.saldo:.2f}",
        }


class SilnikKont:
    def __init__(self) -> None:
        self.konta: list[KontoT] = []
        self._next_konto_id = 1
        self._next_zapis_id = 1

    @staticmethod
    def parse_kwota(raw: str) -> Decimal:
        try:
            value = Decimal(raw.strip().replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError("Niepoprawna kwota.") from exc
        if value <= 0:
            raise ValueError("Kwota musi być dodatnia.")
        return value.quantize(Decimal("0.01"))

    def pobierz_konto(self, konto_id: int) -> KontoT:
        for konto in self.konta:
            if konto.id == konto_id:
                return konto
        raise KeyError("Nie znaleziono konta.")

    def dodaj_konto(self, nazwa: str) -> KontoT:
        nazwa = nazwa.strip()
        if not nazwa:
            raise ValueError("Nazwa konta nie może być pusta.")
        konto = KontoT(id=self._next_konto_id, nazwa=nazwa)
        self._next_konto_id += 1
        self.konta.append(konto)
        return konto

    def zmien_nazwe_konta(self, konto_id: int, nazwa: str) -> KontoT:
        konto = self.pobierz_konto(konto_id)
        nazwa = nazwa.strip()
        if not nazwa:
            raise ValueError("Nazwa konta nie może być pusta.")
        konto.nazwa = nazwa
        return konto

    def usun_konto(self, konto_id: int) -> None:
        self.konta = [k for k in self.konta if k.id != konto_id]

    def dodaj_zapis(self, konto_id: int, strona: str, kwota_raw: str) -> Zapis:
        konto = self.pobierz_konto(konto_id)
        kwota = self.parse_kwota(kwota_raw)
        zapis = konto.dodaj_zapis(self._next_zapis_id, strona, kwota)
        self._next_zapis_id += 1
        return zapis

    def edytuj_zapis(self, konto_id: int, zapis_id: int, strona: str, kwota_raw: str) -> Zapis:
        konto = self.pobierz_konto(konto_id)
        kwota = self.parse_kwota(kwota_raw)
        return konto.edytuj_zapis(zapis_id, strona, kwota)

    def usun_zapis(self, konto_id: int, zapis_id: int) -> None:
        konto = self.pobierz_konto(konto_id)
        konto.usun_zapis(zapis_id)

    def as_dict(self) -> dict:
        return {"konta": [k.as_dict() for k in self.konta]}


def pobierz_kwote() -> Decimal:
    while True:
        raw = input("Kwota: ").strip().replace(",", ".")
        try:
            kwota = Decimal(raw)
            if kwota <= 0:
                print("Kwota musi być dodatnia.")
                continue
            return kwota.quantize(Decimal("0.01"))
        except InvalidOperation:
            print("Niepoprawna kwota. Spróbuj ponownie.")


def main() -> None:
    print("Program do T-kont (CLI)\n")
    silnik = SilnikKont()
    nazwa = input("Podaj nazwę konta: ").strip() or "Konto bez nazwy"
    konto = silnik.dodaj_konto(nazwa)

    while True:
        print("\nWybierz opcję:")
        print("1. Dodaj zapis po stronie Winien")
        print("2. Dodaj zapis po stronie Ma")
        print("3. Pokaż podsumowanie")
        print("4. Zakończ")

        wybor = input("Twój wybór: ").strip()

        if wybor == "1":
            silnik.dodaj_zapis(konto.id, "W", str(pobierz_kwote()))
            print("Dodano zapis po stronie Winien.")
        elif wybor == "2":
            silnik.dodaj_zapis(konto.id, "M", str(pobierz_kwote()))
            print("Dodano zapis po stronie Ma.")
        elif wybor == "3":
            aktualne = silnik.pobierz_konto(konto.id)
            print(f"Suma Winien: {aktualne.suma_winien:.2f}")
            print(f"Suma Ma: {aktualne.suma_ma:.2f}")
            print(f"Saldo: {aktualne.saldo:.2f}")
        elif wybor == "4":
            print("Koniec pracy programu.")
            break
        else:
            print("Nieznana opcja. Wpisz 1, 2, 3 lub 4.")


if __name__ == "__main__":
    main()
