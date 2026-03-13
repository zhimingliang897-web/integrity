import multiprocessing

bind = "0.0.0.0:5000"
workers = 2
worker_class = "sync"
timeout = 300
keepalive = 5
graceful_timeout = 30
errorlog = "-"
accesslog = "-"
loglevel = "info"

# SSE 支持
worker_connections = 1000