#!/bin/bash
# Start Xvfb virtual display in the background
# This gives Chrome a fake "screen" so Turnstile thinks it's a real desktop
Xvfb :99 -screen 0 1280x1024x24 &
export DISPLAY=:99

# Give Xvfb a second to initialize
sleep 1

# Start the Flask app using Gunicorn for production
# We use 1 worker because the Selenium driver is a singleton
# Timeout is set to 60 to prevent Gunicorn from killing the worker if Turnstile takes time
exec gunicorn app:app --workers 1 --bind 0.0.0.0:5000 --timeout 60
