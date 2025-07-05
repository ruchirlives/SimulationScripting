import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils


def test_add():
    assert utils.add(2, 3) == 5
