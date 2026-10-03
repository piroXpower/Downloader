#!/bin/bash
cd /root/omnitube
exec /root/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload
