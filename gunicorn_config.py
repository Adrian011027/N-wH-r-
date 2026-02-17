# Configuración de Gunicorn para producción
import multiprocessing

# Bind: Puerto donde Gunicorn escucha (solo localhost)
bind = "127.0.0.1:8000"

# Workers: Número de procesos worker (2 * CPU cores + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout (segundos para esperar respuesta)
timeout = 120

# Keep-Alive (segundos)
keepalive = 5

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Max requests (reciclaje de workers para evitar memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Preload para cargar la app antes de fork (ahorra memoria)
preload_app = True
