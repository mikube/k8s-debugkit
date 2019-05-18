#!/bin/bash

[ -z "$K8S_DEBUGKIT_DISABLE_DEBUG_MODE" ] \
  && uvicorn k8s-debugkit:api --host 0.0.0.0 --port 80 --reload --log-level debug \
  || uvicorn k8s-debugkit:api --host 0.0.0.0 --port 80

