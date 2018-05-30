from aioapp.config import Config as AioappConfig


class Config(AioappConfig):
    http_host: str
    http_port: int
    db_url: str
    db_pool_min_size: int
    db_pool_max_size: int
    db_pool_max_queries: int
    db_pool_max_inactive_connection_lifetime: float
    db_prepare_connect_max_attempts: int
    db_prepare_connect_retry_interval: float
    rabbit_url: str
    rabbit_heartbeat: int
    rabbit_prepare_connect_max_attempts: int
    rabbit_prepare_connect_retry_interval: float
    tracer_driver: str
    tracer_name: str
    tracer_url: str
    tracer_default_sampled: bool
    metrics_driver: str
    metrics_name: str
    metrics_url: str
    _vars = {
        'http_host': {
            'type': str,
            'name': 'HTTP_HOST',
            'descr': 'HTTP server TCP/IP hostname to serve on',
            'default': '127.0.0.1',
        },
        'http_port': {
            'type': int,
            'name': 'HTTP_PORT',
            'descr': 'HTTP server TCP/IP port to serve on',
            'default': 8080,
            'min': 1,
            'max': 65535,
        },
        'db_url': {
            'type': str,
            'name': 'DB_URL',
            'descr': 'Database connection string in the following format '
                     'postgres://user:pass@host:port/database?option=value',
        },
        'db_pool_min_size': {
            'type': int,
            'name': 'DB_POOL_MIN_SIZE',
            'descr': 'Number of database connection the pool will be '
                     'initialized with',
            'default': 1,
            'min': 1,
        },
        'db_pool_max_size': {
            'type': int,
            'name': 'DB_POOL_MAX_SIZE',
            'descr': 'Max number of database connections in the pool',
            'default': 10,
            'min': 1,
        },
        'db_pool_max_queries': {
            'type': int,
            'name': 'DB_POOL_MAX_QUERIES',
            'descr': 'Number of queries after a database connection is closed'
                     ' and replaced with a new connection',
            'default': 50000,
            'min': 1,
        },
        'db_pool_max_inactive_connection_lifetime': {
            'type': float,
            'name': 'DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME',
            'descr': 'Number of seconds after which inactive database '
                     'connections in the pool will be closed. '
                     'Pass 0 to disable this mechanism.',
            'default': 300.0,
            'min': 0.,
        },
        'db_prepare_connect_max_attempts': {
            'type': int,
            'name': 'DB_PREPARE_CONNECT_MAX_ATTEMPTS',
            'descr': 'Maximum number of attempts to connect to the database',
            'default': 60,
            'min': 1,
        },
        'db_prepare_connect_retry_interval': {
            'type': float,
            'name': 'DB_PREPARE_CONNECT_RETRY_DELAY',
            'descr': 'Interval between connect attempts to the database',
            'default': 1.0,
            'min': 0.001,
        },
        'rabbit_url': {
            'type': str,
            'name': 'RABBIT_URL',
            'descr': 'RabbitMq connection string in the following format '
                     'amqp://user:pass@host:port/vhost',
            'required': True,
            'default': 'amqp://guest:guest@localhost:5672/'
        },
        'rabbit_heartbeat': {
            'type': int,
            'name': 'RABBIT_HEARTBEAT',
            'descr': 'The delay, in seconds, of the RabbitMq connection '
                     'heartbeat that the server wants. Zero means the server '
                     'does not want a heartbeat.',
            'default': 5,
            'min': 0,
        },
        'rabbit_prepare_connect_max_attempts': {
            'type': int,
            'name': 'RABBIT_PREPARE_CONNECT_MAX_ATTEMPTS',
            'descr': 'Maximum number of attempts to connect to the RabbitMq',
            'default': 60,
            'min': 1,
        },
        'rabbit_prepare_connect_retry_interval': {
            'type': float,
            'name': 'RABBIT_PREPARE_CONNECT_RETRY_DELAY',
            'descr': 'Interval between connect attempts to the RabbitMq',
            'default': 1.0,
            'min': 0.001,
        },

        'tracer_driver': {
            'type': str,
            'name': 'TRACER',
        },
        'tracer_name': {
            'type': str,
            'name': 'TRACER_NAME',
            'default': 'myaioapp',
        },
        'tracer_url': {
            'type': str,
            'name': 'TRACER_URL',
        },
        'tracer_default_sampled': {
            'type': bool,
            'name': 'TRACER_DEFAULT_SAMPLED',
            'default': True,
        },
        'metrics_driver': {
            'type': str,
            'name': 'METRICS',
        },
        'metrics_name': {
            'type': str,
            'name': 'METRICS_NAME',
            'default': 'myaioapp_',
        },
        'metrics_url': {
            'type': str,
            'name': 'METRICS_URL',
        },
    }
