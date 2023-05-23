import unittest
from pprint import pprint

import tf_s3backend.algo as sut


class TestAlgos(unittest.TestCase):

    def test_extract(self):
        fix =  {

            "dev":{
                "a" : 1,
                "b" : 1,
                "c" : 100,
                "region" : "north1",
            },
            "stage":{
                "a": 1,
                "x": 1,
                "c": 199,
                "e": 199,
                "region" : "north1",
            },
            "test":{
                "a": 1,
                "x": 1,
                "c": 99,
                "x0": 1,
                "c0": 99,
                "region" : "north1",
            }
        }
        new_data,common = sut.extract_dups(fix)
        assert len(new_data['dev'].keys()) == 2,f"{new_data['dev']=}"
        assert len(new_data['stage'].keys()) == 3,f"{new_data['stage']=}"
        assert len(new_data['test'].keys()) == 4,f"{new_data['test']=}"
        
        assert common == {'a': 1, 'region': 'north1'}, f"{common=}"
