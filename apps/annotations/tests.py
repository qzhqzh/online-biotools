from django.test import SimpleTestCase, Client, override_settings
from pathlib import Path
import tempfile

from apps.annotations.normalize import normalize_variant
from apps.annotations.engines.vep import parse_vep_output
from apps.annotations.engines.annovar import (
    parse_multianno,
    to_avinput_line,
)


class NormalizeTests(SimpleTestCase):
    def test_colon_format(self):
        self.assertEqual(
            normalize_variant("17:43092951 G>A"),
            "17 43092951 43092951 G/A +",
        )

    def test_chr_prefix(self):
        self.assertEqual(
            normalize_variant("chr13:32906732 G>A"),
            "13 32906732 32906732 G/A +",
        )

    def test_hgvs_g(self):
        self.assertEqual(
            normalize_variant("17:g.43092951G>A"),
            "17 43092951 43092951 G/A +",
        )


class ParseVepTests(SimpleTestCase):
    def test_parse_pick_consequence(self):
        raw = [
            {
                "input": "17 43092951 43092951 G/A +",
                "transcript_consequences": [
                    {
                        "variant_allele": "A",
                        "gene_symbol": "BRCA1",
                        "transcript_id": "ENST00000",
                        "consequence_terms": ["missense_variant"],
                        "impact": "MODERATE",
                        "hgvsc": "ENST00000:c.1G>A",
                        "hgvsp": "ENSP00000:p.Gly1Arg",
                        "biotype": "protein_coding",
                        "canonical": 1,
                    }
                ],
            }
        ]
        results = parse_vep_output(raw, {"17 43092951 43092951 G/A +": "17:43092951 G>A"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].gene, "BRCA1")
        self.assertEqual(results[0].input, "17:43092951 G>A")
        self.assertEqual(results[0].canonical, "YES")


class AnnovarUnitTests(SimpleTestCase):
    def test_to_avinput(self):
        original, line = to_avinput_line("17:43092951 G>A")
        self.assertEqual(original, "17:43092951 G>A")
        self.assertEqual(line, "17\t43092951\t43092951\tG\tA")

    def test_parse_multianno(self):
        content = (
            "Chr\tStart\tEnd\tRef\tAlt\tFunc.refGeneWithVer\tGene.refGeneWithVer\t"
            "GeneDetail.refGeneWithVer\tExonicFunc.refGeneWithVer\tAAChange.refGeneWithVer\n"
            "chr17\t43092951\t43092951\tG\tA\texonic\tBRCA1\t.\tmissense\t"
            "BRCA1:NM_007294:exon10:c.1G>A:p.G1R\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.hg38_multianno.txt"
            path.write_text(content, encoding="utf-8")
            results = parse_multianno(
                path, {"17:43092951:43092951:G:A": "17:43092951 G>A"}
            )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].gene, "BRCA1")
        self.assertEqual(results[0].engine, "annovar")
        self.assertIn("c.1G>A", results[0].cdot or "")


class ApiSmokeTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_health_live(self):
        resp = self.client.get("/health/live")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_engines_include_vep_and_annovar(self):
        resp = self.client.get("/api/v1/engines/")
        self.assertEqual(resp.status_code, 200)
        ids = {e["id"] for e in resp.json()["engines"]}
        self.assertEqual(ids, {"vep", "annovar"})

    def test_annotations_validation(self):
        resp = self.client.post(
            "/api/v1/annotations/",
            data={"variants": [], "assembly": "GRCh37"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    @override_settings(ANNOVAR_MODE="local", ANNOVAR_TABLE_BIN="/nonexistent/table_annovar.pl")
    def test_annovar_not_ready_returns_503(self):
        resp = self.client.post(
            "/api/v1/annotations/",
            data={
                "engine": "annovar",
                "assembly": "GRCh38",
                "variants": ["17:43092951 G>A"],
            },
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 503)
