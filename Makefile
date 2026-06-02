PYTHON ?= python3
VENV ?= .venv
HOST ?= 127.0.0.1
KB_PORT ?= 8001
KB_URL ?= http://localhost:$(KB_PORT)

.PHONY: setup build-all docs test lint framework-check framework-drift implementation-drift improvement-queue conversation-feedback conversation-feedback-due harness-check team-reliability release-gate report-html maintenance-daily

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -e ".[dev]"
	@echo "Ready. Run: source $(VENV)/bin/activate"

build-all: lint framework-check test framework-drift improvement-queue report-html harness-check team-reliability release-gate
	$(MAKE) report-html

docs:
	mkdocs serve --dev-addr $(HOST):$(KB_PORT)

test:
	python tools/run_tests_with_report.py

lint:
	ruff check team_framework tests tools

framework-check:
	python tools/validate_agentic_framework.py

framework-drift:
	python tools/check_implementation_drift.py

implementation-drift: framework-drift

improvement-queue:
	python tools/run_improvement_queue.py

conversation-feedback:
	python tools/analyze_conversation_feedback.py --force

conversation-feedback-due:
	python tools/analyze_conversation_feedback.py

harness-check:
	python tools/validate_harness_quality.py

team-reliability:
	python tools/score_team_reliability.py

release-gate:
	python tools/run_release_gate.py

report-html:
	python tools/generate_combined_report_html.py

maintenance-daily:
	mkdir -p state/reports
	$(MAKE) lint
	$(MAKE) framework-check
	$(MAKE) test
	$(MAKE) framework-drift
	$(MAKE) improvement-queue
	$(MAKE) conversation-feedback-due
	$(MAKE) report-html
	$(MAKE) harness-check
	$(MAKE) team-reliability
	$(MAKE) release-gate
	$(MAKE) report-html
