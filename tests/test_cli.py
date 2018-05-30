import copy
import logging
import sys
import os
import pytest
import mock
import myaioapp
from aioapp.config import ConfigError
from myaioapp.cli import parse_argv, setup_logging, Args, main


def test_cli_success():
    args = parse_argv('progname', ['--log-level', 'INFO',
                                   '--log-file', '/tmp/sgsfgsdfg'])
    assert not args.version
    assert args.log_level == 'INFO'
    assert args.log_file == '/tmp/sgsfgsdfg'


def test_cli_bad_log_level(capsys):
    with pytest.raises(SystemExit):
        parse_argv('progname', ['--log-level', 'SUCCESS',
                                '--log-file', '/tmp/sgsfgsdfg'])
    out, err = capsys.readouterr()
    assert '--log-level' in err
    assert 'SUCCESS' in err


def test_cli_success_show_version():
    args = parse_argv('progname', ['-v'])
    assert args.version


def test_cli_setup_logging():
    with mock.patch('logging.basicConfig'):
        level = logging.getLevelName(logging.ERROR)
        args = Args(version=False, config=False,
                    log_level=level, log_file=None)
        setup_logging(args)
        logging.basicConfig.assert_called_once_with(level=logging.ERROR)

    with mock.patch('logging.basicConfig'):
        level = logging.getLevelName(logging.ERROR)
        args = Args(version=False, config=False,
                    log_level=level, log_file='/tmp/qwerty')
        setup_logging(args)
        logging.basicConfig.assert_called_once_with(level=logging.ERROR,
                                                    filename='/tmp/qwerty')


def test_cli_main(capsys):
    old_argv = sys.argv
    old_env = os.environ
    try:
        with mock.patch('myaioapp.app.Application.run', return_value=0):
            sys.argv = ['run.py', '-v']
            assert main() == 0
            out, err = capsys.readouterr()
            assert myaioapp.__version__ in out
            assert myaioapp.app.Application.run.call_count == 0

            sys.argv = ['run.py', '-c']
            assert main() == 0
            out, err = capsys.readouterr()
            assert 'Application environment variables' in out
            assert myaioapp.app.Application.run.call_count == 0

            sys.argv = ['run.py', ]
            assert main() == 0
            out, err = capsys.readouterr()
            assert myaioapp.app.Application.run.call_count == 1

            sys.argv = ['run.py', ]
            os.environ['HTTP_PORT'] = '1234567890'
            assert main() == 1

            assert myaioapp.app.Application.run.call_count == 1
    finally:
        sys.argv = old_argv
        os.environ = old_env
