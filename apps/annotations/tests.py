from django.test import SimpleTestCase, Client

from apps.annotations.normalize import normalize_variant
from apps.annotations.engines.vep import parse_vep_output


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


class ApiSmokeTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_health_live(self):
        resp = self.client.get("/health/live")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_engines(self):
        resp = self.client.get("/api/v1/engines/")
        self.assertEqual(resp.status_code, 200)
        engines = resp.json()["engines"]
        self.assertTrue(any(e["id"] == "vep" for e in engines))

    def test_annotations_validation(self):
        resp = self.client.post(
            "/api/v1/annotations/",
            data={"variants": [], "assembly": "GRCh37"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
