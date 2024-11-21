#!/bin/bash
exec gunicorn --chdir app -b 0.0.0.0:5000 run:app