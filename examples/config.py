DB_HOST = 'localhost'
DB_NAME = 'fakedb'
DB_USER = 'root'
DB_PASS = 's3cr3t'

try:
    from local_config import *
except ImportError:
    pass
