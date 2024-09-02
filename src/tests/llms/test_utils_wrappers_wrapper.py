# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Run `pytest --disable-warnings --cov=comps/llms/utils --cov-report=term --cov-report=html tests/llms` to execute unit test with coverage report.
"""

# FIXME: unit tests not working after rewriting Tomek's code
import unittest
from unittest.mock import MagicMock, patch
from comps.llms.utils.wrappers.wrapper import OPEALlm


class TestOPEALlm(unittest.TestCase):

    @patch('comps.llms.utils.wrappers.wrapper.configparser.ConfigParser')
    @patch('comps.llms.utils.wrappers.wrapper.os')
    @patch('comps.llms.utils.wrappers.wrapper.wrapper_vllm')
    @patch('comps.llms.utils.wrappers.wrapper.wrapper_tgi')
    def test_singleton_pattern(self, mock_wrapper_tgi, mock_wrapper_vllm, mock_os, mock_configparser):
        # Ensure singleton pattern works
        instance1 = OPEALlm()
        instance2 = OPEALlm()
        self.assertIs(instance1, instance2)

    def test_load_config(self):
        with patch('configparser.ConfigParser') as mock_config_parser:
            mock_config = MagicMock()
            mock_config_parser.return_value = mock_config
            
            mock_config.get.side_effect = lambda section, option: {
                ('OPEA_Microservice', 'name'): "test_name",
                ('OPEA_Microservice', 'host'): "test_host",
                ('Service', 'model_name'): "test_model_name",
                ('Service', 'model_server'): "test_model_server",
                ('Service', 'model_server_endpoint'): "test_model_server_endpoint",
                ('Logging', 'log_level'): "DEBUG",
                ('Logging', 'log_path'): "/tmp/test.log"
            }[(section, option)]

            OPEALlm()._load_config()
            self.assertEqual(OPEALlm().name, "test_name")
            self.assertEqual(OPEALlm().host, "test_host")
            self.assertEqual(OPEALlm()._model_name, "test_model_name")
            self.assertEqual(OPEALlm()._model_server, "test_model_server")
            self.assertEqual(OPEALlm()._model_server_endpoint, "test_model_server_endpoint")
            self.assertEqual(OPEALlm().log_level, "DEBUG")
            self.assertEqual(OPEALlm().log_path, "/tmp/test.log")

    def test_validate_config(self):
        with patch('comps.llms.utils.wrappers.wrapper.logging'):
            OPEALlm().name = "test_name"
            OPEALlm().host = "test_host"
            OPEALlm().port = 1234
            OPEALlm()._model_name = "test_model_name"
            OPEALlm()._model_server = "test_model_server"
            OPEALlm()._model_server_endpoint = "test_model_server_endpoint"
            OPEALlm().logger = MagicMock()
            OPEALlm()._validate_config()
            OPEALlm().logger.error.assert_not_called()

            OPEALlm().name = ""
            self.assertRaises(ValueError, OPEALlm()._validate_config)
            OPEALlm().name = "test_name"

            OPEALlm().host = ""
            self.assertRaises(ValueError, OPEALlm()._validate_config)
            OPEALlm().host = "test_host"

            OPEALlm().port = None
            self.assertRaises(ValueError, OPEALlm()._validate_config)
            OPEALlm().port = 1234

            OPEALlm()._model_name = ""
            self.assertRaises(ValueError, OPEALlm()._validate_config)
            OPEALlm()._model_name = "test_model_name"

            OPEALlm()._model_server = ""
            self.assertRaises(ValueError, OPEALlm()._validate_config)
            OPEALlm()._model_server = "test_model_server"

            OPEALlm()._model_server_endpoint = ""
            self.assertRaises(ValueError, OPEALlm()._validate_config)
            OPEALlm()._model_server_endpoint = "test_model_server_endpoint"

            OPEALlm().logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()