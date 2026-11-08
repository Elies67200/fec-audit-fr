"""CLI : python -m fec_audit_fr chemin/vers/fec.txt"""
import argparse
import sys
from pathlib import Path
from .validator import as_json, validate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Contrôles préliminaires d'un FEC français (lecture seule).")
    parser.add_argument("file", type=Path, help="Fichier texte FEC à analyser")
    parser.add_argument("--encoding", default="auto", help="auto, utf-8-sig, cp1252, etc.")
    parser.add_argument("--json", action="store_true", help="Rapport JSON")
    parser.add_argument("--max-issues", type=int, default=200, help="Nombre maximal de problèmes listés")
    args = parser.parse_args(argv)
    try:
        result = validate(args.file, encoding=args.encoding, max_issues=max(0, args.max_issues))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Erreur de lecture : {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(as_json(result))
    else:
        print(f"Fichier : {result['file']} | Lignes : {result['lines']} | Écritures : {result['entries']}")
        print(f"Débit : {result['debit']} | Crédit : {result['credit']} | Écart : {result['difference']}")
        print(f"Anomalies : {result['counts']['error']} erreur(s), {result['counts']['warning']} alerte(s)")
        for issue in result["issues"]:
            print(f"[{issue['severity']}] ligne {issue['line']} - {issue['code']}: {issue['message']}")
        if result["issues_truncated"]:
            print("(Liste tronquée : augmenter --max-issues.)")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
