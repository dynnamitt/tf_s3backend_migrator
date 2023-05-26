import unittest
from pathlib import Path
import tf_s3backend.queries as sut


HERE = Path(__file__).absolute().parent

class TestQueries(unittest.TestCase):

    def test_hcl_kv(self):
        hcl_inp = Path(HERE, "fixture/gen1/test/input.tfvars")
        tsr = sut.parse_file(hcl_inp)
        kv = tsr.key_values()
        print(f"{kv=}")
        assert kv["region"]
        assert kv["acc_nick"]

    def test_make_kv(self):
        make_inp = Path(HERE, "fixture/gen2/Makefile")
        tsr = sut.parse_file(make_inp)
        kv = tsr.key_values()
        print(f"{kv=}")
        assert kv["s_region"]
        assert kv["s_key"]

    def test_hcl_backend(self):
        hcl_backend = Path(HERE, "fixture/gen1/tf-code/state.tf")
        tsr = sut.parse_file(hcl_backend)
        tsr.tf_backend_body_kv()
        
        assert 2 == 1
