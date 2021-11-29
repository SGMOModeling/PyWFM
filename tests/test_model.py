import unittest

from iwfmdll import IWFMModel

class TestIWFMModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        cls._app = IWFMModel()

    @classmethod
    def tearDownClass(cls):
        
        cls._app.kill()

    def test_