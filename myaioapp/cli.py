import os
import sys
import logging
import asyncio
import argparse
from aioapp.config import ConfigError
from .config import Config
from typing import NamedTuple
import myaioapp
import myaioapp.app


class Args(NamedTuple):
    version: bool
    config: bool
    log_level: str
    log_file: str


def parse_argv(prog: str, options: list) -> Args:
    parser = argparse.ArgumentParser(prog=prog)

    parser.add_argument(
        '-v',
        '--version',
        action="store_true",
        default=False,
        help="output version information and exit",
    )

    parser.add_argument(
        '-c',
        '--config',
        action="store_true",
        default=False,
        help="output configuration information and exit",
    )

    parser.add_argument(
        '--log-level',
        dest='log_level',
        type=str,
        default='INFO',
        choices=[
            'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        ],
        help='Logging level',
    )

    parser.add_argument(
        '--log-file',
        dest='log_file',
        type=str,
        help='Logging file name',
    )
    parsed = parser.parse_args(args=options)
    return Args(version=parsed.version, log_level=parsed.log_level,
                log_file=parsed.log_file, config=parsed.config)


def setup_logging(options: Args) -> None:
    config = dict(level=getattr(logging, options.log_level))
    if options.log_file:
        config["filename"] = options.log_file
    logging.basicConfig(**config)


def main() -> int:
    try:
        prog, args = sys.argv[0], sys.argv[1:]
        options = parse_argv(prog, args)
        if options.version:
            print(myaioapp.__version__)
            return 0
        if options.config:
            print('Application environment variables:\n')
            print(Config.as_markdown())
            return 0
        setup_logging(options)
        try:
            config = Config(os.environ)
        except ConfigError as e:
            print(e, file=sys.stderr)
            return 1
        return run(config)
    except KeyboardInterrupt:  # pragma: no cover
        return 0


def run(config: Config) -> int:
    loop = asyncio.get_event_loop()
    app = myaioapp.app.Application(config, loop)
    return app.run()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
