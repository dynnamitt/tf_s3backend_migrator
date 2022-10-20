import unittest
from pathlib import Path
from pprint import pprint

import tf_s3backend_migrator.psudo_workspaces as sut

HERE = Path(__file__).absolute().parent

class TestPWorkspaces(unittest.TestCase):

    def test_gen1(self):
        dir = Path(HERE,"fixture/gen1")
        match_pattern = "%/init.tfvars"
        tf_wrkspcs1 = sut.scan_tf_dir(dir, match_pattern, ["tf-code"])
        self.assertEqual(len(tf_wrkspcs1),3)
        pprint(tf_wrkspcs1)

        match_pattern2 = "input-%.tfvars"
        tf_wrkspcs2 = sut.scan_tf_dir(dir, match_pattern2, ["tf-code"])
        self.assertEqual(len(tf_wrkspcs2),0)

    def test_gen2(self):
        dir = Path(HERE,"fixture/gen2")
        match_pattern = "input-%.tfvars"
        tf_wrkspcs1 = sut.scan_tf_dir(dir, match_pattern, ["tf-code"])
        self.assertEqual(len(tf_wrkspcs1),6)
        pprint(tf_wrkspcs1)

if __name__ == '__main__':
    unittest.main()
