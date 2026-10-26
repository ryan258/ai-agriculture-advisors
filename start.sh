#!/bin/bash

# AI Advisors - Start Script
# Usage: ./start.sh

set -e

ADVISORS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$ADVISORS_ROOT/advisors" start
