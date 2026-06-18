import logging
from contextvars import ContextVar


request_id_var = ContextVar('request_id', default='-')
username_var = ContextVar('username', default='anonymous')


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        record.username = username_var.get()
        return True
