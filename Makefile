PYTHON ?= python3
VENV ?= .venv
HOST ?= 127.0.0.1
KB_PORT ?= 8001
KB_URL ?= http://localhost:$(KB_PORT)
TARGET_ROOT ?= .

.PHONY: setup init-repo dropin-bundle manual-copy-clean repo-work-spec target-check target-drift target-release build-all docs test lint framework-check framework-drift implementation-drift improvement-queue conversation-feedback conversation-feedback-due harness-check team-reliability release-gate report-html maintenance-daily

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -e ".[dev]"
	@echo "Ready. Run: source $(VENV)/bin/activate"

init-repo:
	$(PYTHON) tools/init_repo_profile.py --root "$(TARGET_ROOT)"

dropin-bundle:
	$(PYTHON) tools/export_dropin_bundle.py --clean

manual-copy-clean:
	$(PYTHON) tools/clean_manual_copy.py

repo-work-spec:
	$(PYTHON) tools/manage_repo_work_spec.py --title "$(or $(SPEC_TITLE),repo work)"

target-check:
	$(PYTHON) tools/run_target_commands.py

target-drift:
	$(PYTHON) tools/check_target_drift.py

target-release: target-check target-drift

build-all: lint framework-check test framework-drift improvement-queue report-html harness-check team-reliability release-gate
	$(MAKE) report-html

docs:
	mkdocs serve --dev-addr $(HOST):$(KB_PORT)

test:
	$(PYTHON) tools/run_tests_with_report.py

lint:
	ruff check team_framework tests tools

framework-check:
	$(PYTHON) tools/validate_agentic_framework.py

framework-drift:
	$(PYTHON) tools/check_implementation_drift.py

implementation-drift: framework-drift

improvement-queue:
	$(PYTHON) tools/run_improvement_queue.py

conversation-feedback:
	$(PYTHON) tools/analyze_conversation_feedback.py --force

conversation-feedback-due:
	$(PYTHON) tools/analyze_conversation_feedback.py

harness-check:
	$(PYTHON) tools/validate_harness_quality.py

team-reliability:
	$(PYTHON) tools/score_team_reliability.py

release-gate:
	$(PYTHON) tools/run_release_gate.py

report-html:
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
