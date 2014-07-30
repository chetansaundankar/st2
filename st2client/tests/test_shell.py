import os
import sys
import json
import mock
import logging
import unittest2

from tests import base

from st2client import shell
from st2client.utils import httpclient


LOG = logging.getLogger(__name__)


class TestShell(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestShell, self).__init__(*args, **kwargs)
        self.shell = shell.Shell()

    def setUp(self): 
        # Redirect standard output and error to null. If not, then
        # some of the print output from shell commands will pollute
        # the test output.
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    def tearDown(self):
        # Reset to original stdout and stderr.
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def test_endpoints_default(self):
        base_url = 'http://localhost'
        action_url = 'http://localhost:9101'
        reactor_url = 'http://localhost:9102'
        datastore_url = 'http://localhost:9103'
        args = ['trigger', 'list']
        parsed_args = self.shell.parser.parse_args(args)
        client = self.shell.get_client(parsed_args)
        self.assertEqual(client.endpoints['base'], base_url)
        self.assertEqual(client.endpoints['action'], action_url)
        self.assertEqual(client.endpoints['reactor'], reactor_url)
        self.assertEqual(client.endpoints['datastore'], datastore_url)

    def test_endpoints_base_url(self):
        base_url = 'http://www.st2.com'
        action_url = 'http://www.st2.com:9101'
        reactor_url = 'http://www.st2.com:9102'
        datastore_url = 'http://www.st2.com:9103'
        args = ['--url', base_url, 'trigger', 'list']
        parsed_args = self.shell.parser.parse_args(args)
        client = self.shell.get_client(parsed_args)
        self.assertEqual(client.endpoints['base'], base_url)
        self.assertEqual(client.endpoints['action'], action_url)
        self.assertEqual(client.endpoints['reactor'], reactor_url)
        self.assertEqual(client.endpoints['datastore'], datastore_url)

    def test_endpoints_override(self):
        base_url = 'http://www.st2.com'
        action_url = 'http://www.stackstorm1.com:9101'
        reactor_url = 'http://www.stackstorm2.com:9102'
        datastore_url = 'http://www.stackstorm3.com:9103'
        args = ['--url', base_url,
                '--action-url', action_url,
                '--reactor-url', reactor_url,
                '--datastore-url', datastore_url,
                'trigger', 'list']
        parsed_args = self.shell.parser.parse_args(args)
        client = self.shell.get_client(parsed_args)
        self.assertEqual(client.endpoints['base'], base_url)
        self.assertEqual(client.endpoints['action'], action_url)
        self.assertEqual(client.endpoints['reactor'], reactor_url)
        self.assertEqual(client.endpoints['datastore'], datastore_url)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=\
            base.FakeResponse(json.dumps(base.RESOURCES), 200, 'OK')))
    def test_exit_code_on_success(self):
        argv = ['trigger', 'list']
        self.assertEqual(self.shell.run(argv), 0)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=\
            base.FakeResponse(None, 500, 'INTERNAL SERVER ERROR')))
    def test_exit_code_on_error(self):
        argv = ['trigger', 'list']
        self.assertEqual(self.shell.run(argv), 1)

    def _validate_parser(self, args_list, is_subcommand=True):
        for args in args_list:
            ns = self.shell.parser.parse_args(args)
            func = (self.shell.commands[args[0]].run_and_print
                    if not is_subcommand
                    else self.shell.commands[args[0]].\
                            commands[args[1]].run_and_print)
            self.assertEqual(ns.func, func)

    def test_trigger(self):
        args_list = [
            ['trigger', 'list'],
            ['trigger', 'get', 'abc'],
            ['trigger', 'create', '/tmp/trigger.json'],
            ['trigger', 'update', '123', '/tmp/trigger.json'],
            ['trigger', 'delete', 'abc']
        ]
        self._validate_parser(args_list)

    def test_rule(self):
        args_list = [
            ['rule', 'list'],
            ['rule', 'get', 'abc'],
            ['rule', 'create', '/tmp/rule.json'],
            ['rule', 'update', '123', '/tmp/rule.json'],
            ['rule', 'delete', 'abc']
        ]
        self._validate_parser(args_list)

    def test_action(self):
        args_list = [
            ['action', 'list'],
            ['action', 'get', 'abc'],
            ['action', 'create', '/tmp/action.json'],
            ['action', 'update', '123', '/tmp/action.json'],
            ['action', 'delete', 'abc'],
            ['action', 'execute', '-h'],
            ['action', 'execute', 'abc', '-h'],
            ['action', 'execute', 'abc', '-p', 'command="uname =a"'],
        ]
        self._validate_parser(args_list)

    def test_run(self):
        args_list = [
            ['run', '-h'],
            ['run', 'abc', '-h'],
            ['run', 'remote', 'hosts=192.168.1.1', 'user=st2', 'cmd="ls -l"'],
            ['run', 'remote-fib', 'hosts=192.168.1.1', '3', '8']
        ]
        self._validate_parser(args_list, is_subcommand=False)

    def test_action_execution(self):
        args_list = [
            ['execution', 'list'],
            ['execution', 'get', '123'],
        ]
        self._validate_parser(args_list)

    def test_key(self):
        args_list = [
            ['key', 'list'],
            ['key', 'get', 'abc'],
            ['key', 'create', 'abc', '123'],
            ['key', 'update', 'abc', '456'],
            ['key', 'delete', 'abc'],
            ['key', 'load', '/tmp/keys.json']
        ]
        self._validate_parser(args_list)
