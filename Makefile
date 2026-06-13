VENV ?= .venv
DETECTED_PYTHON := $(shell \
	if [ -x "$(VENV)/bin/python" ]; then printf '%s\n' "$(VENV)/bin/python"; \
	elif command -v python3.12 >/dev/null 2>&1; then command -v python3.12; \
	elif command -v python3.13 >/dev/null 2>&1; then command -v python3.13; \
	elif command -v python3.11 >/dev/null 2>&1; then command -v python3.11; \
	elif command -v python3 >/dev/null 2>&1; then command -v python3; \
	elif command -v python >/dev/null 2>&1; then command -v python; \
	else printf '%s\n' python3; fi)
PYTHON ?= $(DETECTED_PYTHON)
RUFF ?= $(shell if [ -x "$(VENV)/bin/ruff" ]; then printf '%s\n' "$(VENV)/bin/ruff"; else printf '%s\n' ruff; fi)
MKDOCS ?= $(shell if [ -x "$(VENV)/bin/mkdocs" ]; then printf '%s\n' "$(VENV)/bin/mkdocs"; else printf '%s\n' mkdocs; fi)
HOST ?= 127.0.0.1
KB_PORT ?= 8001
KB_URL ?= http://localhost:$(KB_PORT)
TARGET_ROOT ?= .
INSTALL_ROOT_AGENTS ?= 1
ROOT_AGENTS_FLAG := $(if $(filter 0 false no off,$(INSTALL_ROOT_AGENTS)),--skip-root-agents,)

.PHONY: setup check-python init-repo dropin-bundle manual-copy-clean repo-work-spec target-check target-drift target-release build-all docs test lint framework-check framework-drift implementation-drift improvement-queue conversation-feedback conversation-feedback-due harness-check team-reliability release-gate report-html maintenance-daily

check-python:
	$(PYTHON) tools/check_python.py

setup: check-python
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -e ".[dev]"
	@echo "Ready. Run: source $(VENV)/bin/activate"

init-repo: check-python
	$(PYTHON) tools/init_repo_profile.py --root "$(TARGET_ROOT)" $(ROOT_AGENTS_FLAG)

dropin-bundle: check-python
	$(PYTHON) tools/export_dropin_bundle.py --clean

manual-copy-clean: check-python
	$(PYTHON) tools/clean_manual_copy.py

repo-work-spec: check-python
	$(PYTHON) tools/manage_repo_work_spec.py --title "$(or $(SPEC_TITLE),repo work)"

target-check: check-python
	$(PYTHON) tools/run_target_commands.py

target-drift: check-python
	$(PYTHON) tools/check_target_drift.py

target-release: target-check target-drift

build-all: lint framework-check test framework-drift improvement-queue report-html harness-check team-reliability release-gate
	$(MAKE) report-html

docs:
	$(MKDOCS) serve --dev-addr $(HOST):$(KB_PORT)

test: check-python
	$(PYTHON) tools/run_tests_with_report.py

lint:
	$(RUFF) check team_framework tests tools

framework-check: check-python
	$(PYTHON) tools/validate_agentic_framework.py

framework-drift: check-python
	$(PYTHON) tools/check_implementation_drift.py

implementation-drift: framework-drift

improvement-queue: check-python
	$(PYTHON) tools/run_improvement_queue.py

conversation-feedback: check-python
	$(PYTHON) tools/analyze_conversation_feedback.py --force

conversation-feedback-due: check-python
	$(PYTHON) tools/analyze_conversation_feedback.py

harness-check: check-python
	$(PYTHON) tools/validate_harness_quality.py

team-reliability: check-python
	$(PYTHON) tools/score_team_reliability.py

release-gate: check-python
	$(PYTHON) tools/run_release_gate.py

report-html: check-python
	$(PYTHON) tools/generate_combined_report_html.py

maintenance-daily:
	mkdir -p state/reports
	$(MAKE) init-repo
	$(MAKE) lint
	$(MAKE) framework-check
	$(MAKE) test
	$(MAKE) target-check
	$(MAKE) target-drift
	$(MAKE) framework-drift
	$(MAKE) improvement-queue
	$(MAKE) conversation-feedback-due
	$(MAKE) report-html
	$(MAKE) harness-check
	$(MAKE) team-reliability
	$(MAKE) release-gate
	$(MAKE) report-html
