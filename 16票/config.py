# -*- coding: utf-8 -*-
"""
Damai ticket bot configuration.
Edit values based on your target event.
"""

# Target sale time, format: "YYYY-MM-DD HH:MM:SS"
TARGET_TIME = "2026-03-17 12:00:00"

# Start script N minutes before TARGET_TIME
# Script will wait first, then run main.py automatically.
START_SCRIPT_MINUTES_BEFORE = 5

# Ticket count
TICKET_COUNT = 1

# Real-name viewers, must match names in Damai app exactly
VIEWER_NAMES = ["梁致铭"]

# Price priority from high to low (string numbers)
PRICE_PRIORITY = ["380"]

# Session priority, leave empty if not needed
SESSION_PRIORITY = []

# Advanced timing settings
PREPARE_MS = 800
MAX_RETRY = 20
CLICK_INTERVAL = 50
PAGE_TIMEOUT = 10

# Debug screenshot settings
SAVE_SCREENSHOTS = True
SCREENSHOT_DIR = "screenshots"

# Mode: "normal" or "rush"
MODE = "normal"

# Damai package info
DAMAI_PACKAGE = "cn.damai"
DAMAI_ACTIVITY = "cn.damai.homepage.MainActivity"
