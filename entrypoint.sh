#!/bin/bash

cd backend/python && python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 &
rabbitmq-server -detached &
cd backend/elixir && mix phx.server