import unittest
from unittest.mock import patch, MagicMock
import logging
import sys
import os
import configparser

from proxlb import (
    initialize_logger,
    pre_validations,
    post_validations,
    validate_daemon,
    __validate_imports,
    __validate_config_file,
    initialize_args,
    initialize_config_path,
    initialize_config_options,
    api_connect,
    get_node_statistics,
    get_vm_statistics,
    balancing_calculations,
    __get_node_most_free_values,
    run_vm_rebalancing,
    SystemdHandler,
    __errors__
)

class TestProxLB(unittest.TestCase):

    def test_initialize_logger(self):
        with patch('logging.getLogger') as mock_get_logger, patch('logging.Handler'):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            initialize_logger(logging.DEBUG, SystemdHandler())
            mock_logger.setLevel.assert_called_with(logging.DEBUG)
            self.assertTrue(mock_logger.addHandler.called)

    def test_pre_validations(self):
        with patch('proxlb.__validate_imports') as mock_validate_imports, patch('proxlb.__validate_config_file') as mock_validate_config_file:
            pre_validations('/path/to/config')
            self.assertTrue(mock_validate_imports.called)
            mock_validate_config_file.assert_called_with('/path/to/config')

    def test_post_validations(self):
        global __errors__
        __errors__ = False
        with patch('logging.critical') as mock_critical, patch('logging.info') as mock_info:
            post_validations()
            self.assertTrue(mock_info.called)
            self.assertFalse(mock_critical.called)

        __errors__ = True
        with patch('logging.critical') as mock_critical, patch('logging.info'):
            post_validations()
            self.assertTrue(mock_critical.called)

    def test_validate_daemon(self):
        with patch('logging.info') as mock_info, patch('time.sleep') as mock_sleep, patch('sys.exit') as mock_exit:
            validate_daemon(1, 1)
            self.assertTrue(mock_info.called)
            self.assertTrue(mock_sleep.called)

            validate_daemon(0, 1)
            self.assertTrue(mock_exit.called)

    def test_validate_imports(self):
        global _imports
        _imports = True
        with patch('logging.critical') as mock_critical, patch('logging.info') as mock_info, patch('sys.exit') as mock_exit:
            __validate_imports()
            self.assertTrue(mock_info.called)
            self.assertFalse(mock_exit.called)
            self.assertFalse(mock_critical.called)

        _imports = False
        with patch('logging.critical') as mock_critical, patch('logging.info'), patch('sys.exit') as mock_exit:
            __validate_imports()
            self.assertTrue(mock_critical.called)
            self.assertTrue(mock_exit.called)

    def test_validate_config_file(self):
        with patch('os.path.isfile', return_value=True), patch('logging.critical') as mock_critical, patch('logging.info') as mock_info, patch('sys.exit') as mock_exit:
            __validate_config_file('/path/to/config')
            self.assertTrue(mock_info.called)
            self.assertFalse(mock_exit.called)
            self.assertFalse(mock_critical.called)

        with patch('os.path.isfile', return_value=False), patch('logging.critical') as mock_critical, patch('logging.info'), patch('sys.exit') as mock_exit:
            __validate_config_file('/path/to/config')
            self.assertTrue(mock_critical.called)
            self.assertTrue(mock_exit.called)

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(config='/path/to/config'))
    def test_initialize_args(self, mock_parse_args):
        args = initialize_args()
        self.assertEqual(args.config, '/path/to/config')

    def test_initialize_config_path(self):
        app_args = MagicMock(config='/path/to/config')
        with patch('logging.info') as mock_info:
            config_path = initialize_config_path(app_args)
            self.assertEqual(config_path, '/path/to/config')
            self.assertTrue(mock_info.called)

        app_args.config = None
        with patch('logging.info') as mock_info:
            config_path = initialize_config_path(app_args)
            self.assertEqual(config_path, '/etc/proxlb/proxlb.conf')
            self.assertTrue(mock_info.called)

    @patch('configparser.ConfigParser.read', side_effect=lambda x: setattr(configparser.ConfigParser(), 'proxmox', {'api_host': 'host', 'api_user': 'user', 'api_pass': 'pass', 'verify_ssl': '0'}))
    def test_initialize_config_options(self, mock_read):
        with patch('logging.info') as mock_info, patch('sys.exit') as mock_exit:
            config_path = '/path/to/config'
            proxmox_api_host, proxmox_api_user, proxmox_api_pass, proxmox_api_ssl_v, balancing_method, ignore_nodes, ignore_vms, daemon, schedule = initialize_config_options(config_path)
            self.assertEqual(proxmox_api_host, 'host')
            self.assertEqual(proxmox_api_user, 'user')
            self.assertEqual(proxmox_api_pass, 'pass')
            self.assertEqual(proxmox_api_ssl_v, '0')
            self.assertTrue(mock_info.called)
            self.assertFalse(mock_exit.called)

    @patch('proxmoxer.ProxmoxAPI')
    def test_api_connect(self, mock_proxmox_api):
        with patch('requests.packages.urllib3.disable_warnings') as mock_disable_warnings, patch('logging.warning') as mock_warning, patch('logging.info') as mock_info:
            proxmox_api_ssl_v = 0
            api_object = api_connect('host', 'user', 'pass', proxmox_api_ssl_v)
            self.assertTrue(mock_disable_warnings.called)
            self.assertTrue(mock_warning.called)
            self.assertTrue(mock_info.called)
            self.assertTrue(mock_proxmox_api.called)

    def test_get_node_statistics(self):
        mock_api_object = MagicMock()
        mock_api_object.nodes.get.return_value = [{'node': 'node1', 'status': 'online', 'maxcpu': 100, 'cpu': 50, 'maxmem': 1000, 'mem': 500, 'maxdisk': 10000, 'disk': 5000}]
        node_statistics = get_node_statistics(mock_api_object, '')
        self.assertIn('node1', node_statistics)
        self.assertEqual(node_statistics['node1']['cpu_total'], 100)
        self.assertEqual(node_statistics['node1']['cpu_used'], 50)
        self.assertEqual(node_statistics['node1']['memory_total'], 1000)
        self.assertEqual(node_statistics['node1']['memory_used'], 500)
        self.assertEqual(node_statistics['node1']['disk_total'], 10000)
        self.assertEqual(node_statistics['node1']['disk_used'], 5000)

    def test_get_vm_statistics(self):
        mock_api_object = MagicMock()
        mock_api_object.nodes.get.return_value = [{'node': 'node1', 'status': 'online'}]
        mock_api_object.nodes().qemu.get.return_value = [{'name': 'vm1', 'status': 'running', 'cpus': 4, 'cpu': 2, 'maxmem': 8000, 'mem': 4000, 'maxdisk': 20000, 'disk': 10000, 'vmid': 101}]
        vm_statistics = get_vm_statistics(mock_api_object, '')
        self.assertIn('vm1', vm_statistics)
        self.assertEqual(vm_statistics['vm1']['cpu_total'], 4)
        self.assertEqual(vm_statistics['vm1']['cpu_used'], 2)
        self.assertEqual(vm_statistics['vm1']['memory_total'], 8000)
        self.assertEqual(vm_statistics['vm1']['memory_used'], 4000)
        self.assertEqual(vm_statistics['vm1']['disk_total'], 20000)
        self.assertEqual(vm_statistics['vm1']['disk_used'], 10000)
        self.assertEqual(vm_statistics['vm1']['vmid'], 101)
        self.assertEqual(vm_statistics['vm1']['node_parent'], 'node1')

    def test_balancing_calculations(self):
        node_statistics = {
            'node1': {'cpu_free': 80, 'memory_free': 8000, 'disk_free': 80000},
            'node2': {'cpu_free': 70, 'memory_free': 7000, 'disk_free': 70000}
        }
        vm_statistics = {
            'vm1': {'cpu_used': 20, 'memory_used': 2000, 'disk_used': 20000, 'node_parent': 'node1'},
            'vm2': {'cpu_used': 30, 'memory_used': 3000, 'disk_used': 30000, 'node_parent': 'node1'}
        }
        with patch('logging.info') as mock_info, patch('logging.error') as mock_error:
            node_statistics_rebalanced, vm_statistics_rebalanced = balancing_calculations('memory', node_statistics, vm_statistics)
            self.assertTrue(mock_info.called)
            self.assertFalse(mock_error.called)
            self.assertEqual(vm_statistics_rebalanced['vm1']['node_rebalance'], 'node2')
            self.assertEqual(vm_statistics_rebalanced['vm2']['node

