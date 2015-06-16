from mock import patch

from clusterous.clusterous import *

class TestClusterous:

    @patch.object(Clusterous, '_read_config')
    def test_init(self, read_config):
        c = Clusterous()
        read_config.assert_called_once()


