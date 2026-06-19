"""
Phase 5: Gunicorn Configuration
HomeMade Pickles & Snacks - Production Server
"""

bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
timeout = 120
accesslog = "/var/log/pickles_snacks/access.log"
errorlog = "/var/log/pickles_snacks/error.log"
loglevel = "info"
