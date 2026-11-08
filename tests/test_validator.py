import tempfile
import unittest
from pathlib import Path
from fec_audit_fr.validator import HEADERS, validate


def line(num, account, debit, credit, date="20261031"):
    values = ["OD", "Opérations diverses", num, date, account, "Libellé compte", "", "",
              f"P{num}", date, "Opération fictive", debit, credit, "", "", date, "", ""]
    return "\t".join(values)


class FecValidationTests(unittest.TestCase):
    def make(self, content, encoding="utf-8"):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / "fichier.txt"
        path.write_text(content, encoding=encoding)
        return path

    def content(self, *lines):
        return "\t".join(HEADERS) + "\n" + "\n".join(lines) + "\n"

    def test_valid(self):
        result = validate(self.make(self.content(line("1", "606", "50,00", "0,00"),
                                                       line("1", "401", "0,00", "50,00"))))
        self.assertTrue(result["ok"])
        self.assertEqual(result["entries"], 1)
        self.assertEqual(result["difference"], "0.00")

    def test_unbalanced(self):
        result = validate(self.make(self.content(line("1", "606", "51,00", "0,00"),
                                                       line("1", "401", "0,00", "50,00"))))
        self.assertFalse(result["ok"])
        self.assertIn("UNBALANCED_ENTRY", {i["code"] for i in result["issues"]})

    def test_non_regulatory_date_format(self):
        result = validate(self.make(self.content(line("1", "606", "5,00", "0,00", "31/10/2026"),
                                                       line("1", "401", "0,00", "5,00", "31/10/2026"))))
        self.assertFalse(result["ok"])
        self.assertIn("DATE", {i["code"] for i in result["issues"]})

    def test_cp1252(self):
        content = self.content(line("1", "606", "5,00", "0,00"), line("1", "401", "0,00", "5,00"))
        content = content.replace("Opération fictive", "Écriture café")
        result = validate(self.make(content, encoding="cp1252"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["encoding"], "cp1252")

    def test_bad_columns(self):
        result = validate(self.make(self.content("\t".join(["x"] * 17))))
        self.assertFalse(result["ok"])
        self.assertIn("COLUMN_COUNT", {i["code"] for i in result["issues"]})

    def test_extra_field_allowed(self):
        header = "\t".join(HEADERS + ("ChampExtra",))
        content = header + "\n" + line("1", "606", "3,00", "0,00") + "\tx\n" + line("1", "401", "0,00", "3,00") + "\tx\n"
        result = validate(self.make(content))
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
