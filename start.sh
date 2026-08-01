#!/bin/bash

# Start the Flask app using Gunicorn for production
# We use 1 worker because the Selenium driver is a singleton
# Timeout is set to 60 to prevent Gunicorn from killing the worker if Turnstile takes time
exec gunicorn app:app --workers 1 --bind 0.0.0.0:5000 --timeout 60
