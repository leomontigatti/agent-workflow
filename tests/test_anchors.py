"""Tests for skills/domain-modeling/scripts/anchors.py: an ADR or a glossary term whose anchor left the code."""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
SCRIPT = os.path.join(ROOT, "skills/domain-modeling/scripts/anchors.py")


class Anchors(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work = tmp.name
        # No user or system git config: a signing or hooks setting there would break the fixture.
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        subprocess.run(["git", "-C", self.work, "init", "-q"], check=True, env=self.env)

    def write(self, path, text):
        full = os.path.join(self.work, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def run_script(self):
        return subprocess.run([sys.executable, "-I", SCRIPT], cwd=self.work, capture_output=True, text=True, env=self.env)

    def test_a_governed_path_in_the_tree_passes(self):
        self.write("app/billing/sql.py", "x = 1\n")
        self.write("docs/adr/0001-manual-sql.md", "# Manual SQL\n\nNo ORM in billing.\n\nGoverns: `app/billing/`, `app/*/sql.py`\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("anchors: ok", run.stdout)

    def test_a_governed_path_that_left_the_tree_is_gone(self):
        self.write("app/orders/sql.py", "x = 1\n")
        self.write("docs/adr/0001-manual-sql.md", "# Manual SQL\n\nNo ORM in billing.\n\nGoverns: `app/billing/`\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 1)
        self.assertIn("gone: docs/adr/0001-manual-sql.md governs `app/billing/`", run.stdout)

    def test_a_governed_file_deleted_but_still_in_the_index_is_gone(self):
        self.write("app/billing/sql.py", "x = 1\n")
        self.write("docs/adr/0001-manual-sql.md", "# Manual SQL\n\nNo ORM in billing.\n\nGoverns: `app/billing/`\n")
        subprocess.run(["git", "-C", self.work, "add", "-A"], check=True, env=self.env)
        os.unlink(os.path.join(self.work, "app/billing/sql.py"))
        run = self.run_script()
        self.assertEqual(run.returncode, 1)
        self.assertIn("governs `app/billing/`", run.stdout)

    def test_a_governed_identifier_inside_a_longer_name_is_gone(self):
        self.write("app/bus.py", "class EventBusPreview: pass\n")
        self.write("docs/adr/0001-events.md", "# Events\n\nContexts talk through events.\n\nGoverns: `EventBus`\n")
        self.assertIn("governs `EventBus`", self.run_script().stdout)

    def test_a_governed_identifier_inside_a_longer_non_ascii_name_is_gone(self):
        self.write("app/models.py", "factura_electrónica = 1\n")
        self.write("docs/adr/0001-facturas.md", "# Facturas\n\nOne table.\n\nGoverns: `factura_electr`\n")
        self.assertIn("governs `factura_electr`", self.run_script().stdout)

    def test_a_governed_path_with_a_non_ascii_name_passes(self):
        self.write("app/facturación.py", "x = 1\n")
        self.write("docs/adr/0001-facturas.md", "# Facturas\n\nOne table.\n\nGoverns: `app/facturación.py`\n")
        subprocess.run(["git", "-C", self.work, "add", "-A"], check=True, env=self.env)
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_an_acronym_term_is_found_in_snake_case(self):
        self.write("GLOSSARY.md", "# Shop\n\n**`XMLInvoice`** — ui: \"Factura\"\nAn invoice.\n")
        self.write("app/models.py", "xml_invoice = 1\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_a_term_with_a_non_ascii_letter_is_found(self):
        self.write("GLOSSARY.md", "# Shop\n\n**`factura_electrónica`** — ui: \"Factura\"\nAn invoice.\n")
        self.write("app/models.py", "factura_electrónica = 1\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_a_governed_identifier_must_be_in_the_code_not_only_in_the_adr(self):
        self.write("app/bus.py", "class EventBus: pass\n")
        self.write("docs/adr/0001-events.md", "# Events\n\nContexts talk through events.\n\nGoverns: `EventBus`, `OutboxRelay`\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 1)
        self.assertNotIn("`EventBus`", run.stdout)
        self.assertIn("gone: docs/adr/0001-events.md governs `OutboxRelay`", run.stdout)

    def test_an_adr_with_no_governs_line_is_listed_and_passes(self):
        self.write("docs/adr/0001-no-aws.md", "# No AWS\n\nCompliance rules it out.\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("no anchor: docs/adr/0001-no-aws.md", run.stdout)

    def test_a_term_is_found_under_another_casing_and_an_untracked_file(self):
        self.write("GLOSSARY.md", "# Shop\n\n**`sale_order`** — ui: \"Pedido\"\nAn order.\n")
        self.write("app/models.py", "class SaleOrder: pass\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_a_term_the_code_no_longer_names_is_gone_and_a_retired_one_is_skipped(self):
        self.write("GLOSSARY.md", "# Shop\n\n**`invoice`** — ui: \"Factura\"\nA request for payment.\n\n"
                                  "**`cliente`** _(retired term)_ — no code identifier\nReplaced by customer.\n")
        self.write("app/models.py", "class Order: pass\n")
        self.write("docs/notes.md", "An invoice is sent after delivery.\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 1)
        self.assertIn("gone: GLOSSARY.md term `invoice`", run.stdout)
        self.assertNotIn("cliente", run.stdout)

    def test_a_file_that_is_not_a_numbered_adr_is_not_read(self):
        self.write("docs/adr/README.md", "# Decisions\n\nGoverns: `app/gone/`\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertNotIn("README.md", run.stdout)

    def test_a_term_only_inside_a_longer_name_is_gone(self):
        self.write("GLOSSARY.md", "# Clinic\n\n**`clinicalRecord`** — ui: \"Historia\"\nA record.\n")
        self.write("app/models.py", "keepsClinicalRecords = True\nclinical_record_id = 1\n")
        self.write("config.yml", "keeps-clinical-records: true\n")
        self.assertIn("gone: GLOSSARY.md term `clinicalRecord`", self.run_script().stdout)

    def test_a_term_only_as_spaced_words_is_gone(self):
        self.write("GLOSSARY.md", "# Clinic\n\n**`replyExample`** — ui: \"Ejemplo\"\nAn example.\n")
        self.write("app/models.py", "# store one reply example per template\nexamples = []\n")
        self.assertIn("gone: GLOSSARY.md term `replyExample`", self.run_script().stdout)

    def test_a_term_is_found_in_its_plural(self):
        self.write("GLOSSARY.md", "# Shop\n\n**`order`** — ui: \"Pedido\"\nAn order.\n\n**`box`** — ui: \"Caja\"\nA box.\n")
        self.write("app/schema.sql", "create table orders (id int);\ncreate table boxes (id int);\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_a_glossary_with_no_readable_term_says_so(self):
        self.write("GLOSSARY.md", "# Shop\n\n**Retail Store**:\nA physical store.\n")
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("no terms: GLOSSARY.md", run.stdout)

    def test_a_project_with_neither_file_passes(self):
        self.write("app/models.py", "x = 1\n")
        self.assertEqual(self.run_script().returncode, 0)


if __name__ == "__main__":
    unittest.main()
