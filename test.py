import delicious2fluid
import unittest

# Generic test user created on the FluidDB Sandbox for the express purpose of
# running unit tests
USERNAME = 'test'
PASSWORD = 'test'

class TestDelisious2Fluid(unittest.TestCase):
    """
    The names of the test methods are pretty self-explanatory. I've made sure
    to comment what's I'm testing if there are various test cases.
    """

    def setUp(self):
        # Only test against the SANDBOX
        fluiddb.instance = fluiddb.SANDBOX
        fluiddb.logout()
