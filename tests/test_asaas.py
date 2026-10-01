import sys, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from integracoes.asaas import AsaasClient, AsaasError


class T(unittest.TestCase):
    def test_cobranca_monta_payload_e_erro(self):
        c = AsaasClient(api_key="x", ambiente="sandbox")
        resp = mock.Mock(ok=True, status_code=200); resp.json.return_value = {"id": "pay_1"}
        with mock.patch.object(c.s, "request", return_value=resp) as r:
            self.assertEqual(c.criar_cobranca("cus_1", 10, "2026-11-10", "PIX")["id"], "pay_1")
            self.assertEqual(r.call_args.kwargs["json"]["billingType"], "PIX")
            self.assertTrue(r.call_args.args[1].startswith("https://api-sandbox"))
        bad = mock.Mock(ok=False, status_code=400); bad.json.return_value = {"errors": []}
        with mock.patch.object(c.s, "request", return_value=bad):
            with self.assertRaises(AsaasError):
                c.consultar_cobranca("x")

if __name__ == "__main__":
    unittest.main()
