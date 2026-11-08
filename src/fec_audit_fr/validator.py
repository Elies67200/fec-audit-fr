"""Contrôles structurels et arithmétiques d'un fichier FEC (18 champs).

Les contrôles ne remplacent ni le Test Compta Demat de la DGFiP, ni une revue
comptable. Aucune écriture n'est créée ou modifiée.
"""
from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

HEADERS = (
    "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
    "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib", "PieceRef",
    "PieceDate", "EcritureLib", "Debit", "Credit", "EcritureLet",
    "DateLet", "ValidDate", "Montantdevise", "Idevise",
)
DECIMAL_ZERO = Decimal("0.00")


def _date(value: str) -> bool:
    if len(value) != 8 or not value.isascii() or not value.isdigit():
        return False
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        return False
    return True


def _number(value: str) -> Decimal:
    # Les séparateurs de milliers ne sont volontairement pas tolérés.
    raw = value.strip().replace(",", ".")
    if not raw or raw.count(".") > 1 or " " in raw:
        raise InvalidOperation
    parsed = Decimal(raw)
    if not parsed.is_finite():
        raise InvalidOperation
    return parsed


def _decode(path: Path, encoding: str) -> tuple[str, str]:
    data = path.read_bytes()
    for enc in ([encoding] if encoding != "auto" else ["utf-8-sig", "cp1252"]):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            pass
    raise UnicodeError("Encodage non reconnu : essayer --encoding cp1252")


def _delimiter(header_line: str) -> str:
    return max(("\t", "|", ";"), key=lambda sep: header_line.count(sep))


def validate(path: str | Path, *, encoding: str = "auto", max_issues: int = 200) -> dict:
    path = Path(path)
    contents, used_encoding = _decode(path, encoding)
    first = contents.splitlines()
    sep = _delimiter(first[0]) if first else "\t"
    reader = csv.reader(io.StringIO(contents, newline=""), delimiter=sep)
    issues: list[dict] = []
    counts = {"error": 0, "warning": 0}

    def flag(severity: str, line: int, code: str, message: str) -> None:
        counts[severity] += 1
        if len(issues) < max_issues:
            issues.append({"severity": severity, "line": line, "code": code, "message": message})

    rows = iter(reader)
    header = next(rows, [])
    if len(header) < 18 or tuple(header[:18]) != HEADERS:
        flag("error", 1, "HEADER", "Les 18 premières colonnes doivent suivre exactement la nomenclature réglementaire, dans l'ordre.")
    if any(not field.strip() for field in header):
        flag("error", 1, "EMPTY_HEADER", "Une colonne possède un nom vide.")

    line_count = 0
    tot_debit = DECIMAL_ZERO
    tot_credit = DECIMAL_ZERO
    entries: dict[tuple[str, str], list[Decimal]] = defaultdict(lambda: [DECIMAL_ZERO, DECIMAL_ZERO])
    journals: dict[str, list[Decimal]] = defaultdict(lambda: [DECIMAL_ZERO, DECIMAL_ZERO])
    for line_number, row in enumerate(rows, start=2):
        if not row or all(not cell.strip() for cell in row):
            continue
        line_count += 1
        if len(row) != len(header):
            flag("error", line_number, "COLUMN_COUNT", f"{len(row)} colonnes, au lieu de {len(header)}.")
            continue
        if len(row) < 18:
            continue
        record = dict(zip(HEADERS, row[:18]))
        for key in ("JournalCode", "EcritureNum", "CompteNum"):
            if not record[key].strip():
                flag("error", line_number, "MISSING_FIELD", f"Champ obligatoire non renseigné : {key}.")
        if not record["EcritureLib"].strip():
            flag("warning", line_number, "EMPTY_LABEL", "Libellé d'écriture vide.")
        if not record["PieceRef"].strip():
            flag("warning", line_number, "EMPTY_PIECE_REF", "Référence de pièce vide : à justifier selon le contexte.")
        for key in ("EcritureDate", "PieceDate", "ValidDate"):
            if not _date(record[key].strip()):
                flag("error", line_number, "DATE", f"{key} doit être une date valide au format AAAAMMJJ.")
        if record["DateLet"].strip() and not _date(record["DateLet"].strip()):
            flag("error", line_number, "DATE", "DateLet renseigné mais invalide.")
        amounts: list[Decimal] = []
        bad_amount = False
        for key in ("Debit", "Credit"):
            try:
                amounts.append(_number(record[key]))
            except InvalidOperation:
                flag("error", line_number, "AMOUNT", f"Montant non numérique ou manquant : {key}.")
                bad_amount = True
        if record["Montantdevise"].strip():
            try:
                _number(record["Montantdevise"])
            except InvalidOperation:
                flag("error", line_number, "CURRENCY_AMOUNT", "Montantdevise invalide.")
        if record["Montantdevise"].strip() and not record["Idevise"].strip():
            flag("warning", line_number, "CURRENCY_CODE", "Montantdevise renseigné sans Idevise.")
        if bad_amount:
            continue
        debit, credit = amounts
        if debit != 0 and credit != 0:
            flag("warning", line_number, "BOTH_SIDES", "Débit et crédit simultanément non nuls sur une ligne.")
        if debit == credit == 0:
            flag("warning", line_number, "ZERO_LINE", "Ligne à débit et crédit nuls.")
        tot_debit += debit
        tot_credit += credit
        key = record["JournalCode"], record["EcritureNum"]
        entries[key][0] += debit
        entries[key][1] += credit
        journals[record["JournalCode"]][0] += debit
        journals[record["JournalCode"]][1] += credit

    for (journal, number), (debit, credit) in sorted(entries.items()):
        if abs(debit - credit) > Decimal("0.005"):
            flag("error", 0, "UNBALANCED_ENTRY", f"Écriture {journal}/{number} déséquilibrée : débit {debit}, crédit {credit}.")
    if abs(tot_debit - tot_credit) > Decimal("0.005"):
        flag("error", 0, "UNBALANCED_FILE", "Le fichier est globalement déséquilibré.")
    if line_count == 0:
        flag("error", 0, "EMPTY_FILE", "Aucune ligne comptable trouvée.")

    return {
        "file": path.name,
        "encoding": used_encoding,
        "separator": {"\t": "tabulation", "|": "pipe", ";": "point-virgule"}[sep],
        "lines": line_count,
        "entries": len(entries),
        "debit": str(tot_debit),
        "credit": str(tot_credit),
        "difference": str(tot_debit - tot_credit),
        "counts": counts,
        "ok": counts["error"] == 0,
        "issues": issues,
        "issues_truncated": sum(counts.values()) > len(issues),
        "journals": {k: {"debit": str(v[0]), "credit": str(v[1])} for k, v in sorted(journals.items())},
    }


def as_json(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)
