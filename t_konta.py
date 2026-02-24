#!/usr/bin/env python3
"""Prosty program CLI do ewidencji kont w układzie T."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


@dataclass
class KontoT:
    nazwa: str
    winien: list[Decimal] = field(default_factory=list)
    ma: list[Decimal] = field(default_factory=list)

    def dodaj_zapis(self, strona: str, kwota: Decimal) -> None:
        if strona == "W":
            self.winien.append(kwota)
        elif strona == "M":
            self.ma.append(kwota)
        else:
            raise ValueError("Strona musi być 'W' (Winien) lub 'M' (Ma).")

    @property
    def suma_winien(self) -> Decimal:
        return sum(self.winien, start=Decimal("0"))

    @property
    def suma_ma(self) -> Decimal:
        return sum(self.ma, start=Decimal("0"))

    @property
    def saldo(self) -> Decimal:
        return self.suma_winien - self.suma_ma

    def drukuj(self) -> str:
        linia = "-" * 54
        strony = [f"{self.nazwa:^54}", linia, f"{'WINIEN':<27}|{'MA':<27}"]
        maks = max(len(self.winien), len(self.ma), 1)

        for i in range(maks):
            w = f"{self.winien[i]:.2f}" if i < len(self.winien) else ""
            m = f"{self.ma[i]:.2f}" if i < len(self.ma) else ""
            strony.append(f"{w:<27}|{m:<27}")

        strony.append(linia)
        strony.append(f"{'Suma':<12}{self.suma_winien:>15.2f}|{'Suma':<12}{self.suma_ma:>15.2f}")

        if self.saldo > 0:
            strony.append(f"Saldo końcowe: {self.saldo:.2f} po stronie WINIEN")
        elif self.saldo < 0:
            strony.append(f"Saldo końcowe: {abs(self.saldo):.2f} po stronie MA")
        else:
            strony.append("Saldo końcowe: 0.00 (konto zbilansowane)")

        return "\n".join(strony)


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
    print("Program do T-kont (księgowość)\n")
    nazwa = input("Podaj nazwę konta: ").strip() or "Konto bez nazwy"
    konto = KontoT(nazwa=nazwa)

    while True:
        print("\nWybierz opcję:")
        print("1. Dodaj zapis po stronie Winien")
        print("2. Dodaj zapis po stronie Ma")
        print("3. Pokaż konto T")
        print("4. Zakończ")

        wybor = input("Twój wybór: ").strip()

        if wybor == "1":
            konto.dodaj_zapis("W", pobierz_kwote())
            print("Dodano zapis po stronie Winien.")
        elif wybor == "2":
            konto.dodaj_zapis("M", pobierz_kwote())
            print("Dodano zapis po stronie Ma.")
        elif wybor == "3":
            print("\n" + konto.drukuj())
        elif wybor == "4":
            print("Koniec pracy programu.")
            break
        else:
            print("Nieznana opcja. Wpisz 1, 2, 3 lub 4.")


if __name__ == "__main__":
    main()
