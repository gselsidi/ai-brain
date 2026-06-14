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
AI_BRAIN_DATA_ROOT ?= $(TARGET_ROOT)
AI_BRAIN_PROFILE ?= $(AI_BRAIN_DATA_ROOT)/state/ai_brain_repo_profile.local.json
AI_BRAIN_MEMORY ?= $(AI_BRAIN_DATA_ROOT)/memory/PROJECT_MEMORY.md
AI_BRAIN_STATE ?= $(AI_BRAIN_DATA_ROOT)/state/sdlc_state.json
AI_BRAIN_REPORT_DIR ?= $(AI_BRAIN_DATA_ROOT)/state/reports
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
	$(PYTHON) tools/init_repo_profile.py --root "$(TARGET_ROOT)" --data-root "$(AI_BRAIN_DATA_ROOT)" --profile "$(AI_BRAIN_PROFILE)" --memory "$(AI_BRAIN_MEMORY)" --state "$(AI_BRAIN_STATE)" $(ROOT_AGENTS_FLAG)

dropin-bundle: check-python
	$(PYTHON) tools/export_dropin_bundle.py --clean

manual-copy-clean: check-python
	$(PYTHON) tools/clean_manual_copy.py

repo-work-spec: check-python
	$(PYTHON) tools/manage_repo_work_spec.py --title "$(or $(SPEC_TITLE),repo work)" --profile "$(AI_BRAIN_PROFILE)" --state "$(AI_BRAIN_STATE)"

target-check: check-python
	$(PYTHON) tools/run_target_commands.py --profile "$(AI_BRAIN_PROFILE)" --output "$(AI_BRAIN_REPORT_DIR)/target-command_report.json"

target-drift: check-python
	$(PYTHON) tools/check_target_drift.py --profile "$(AI_BRAIN_PROFILE)" --state "$(AI_BRAIN_STATE)" --output "$(AI_BRAIN_REPORT_DIR)/target-drift_report.json"

target-release: target-check target-drift

build-all: lint framework-check test framework-drift improvement-queue report-html harness-check team-reliability release-gate
	$(MAKE) report-html

docs:
	$(MKDOCS) serve --dev-addr $(HOST):$(KB_PORT)

test: check-python
	$(PYTHON) tools/run_tests_with_report.py --report-path "$(AI_BRAIN_REPORT_DIR)/test_report.json"

lint:
	$(RUFF) check team_framework tests tools

framework-check: check-python
	$(PYTHON) tools/validate_agentic_framework.py --output "$(AI_BRAIN_REPORT_DIR)/agent-skills-framework_report.json"

framework-drift: check-python
	$(PYTHON) tools/check_implementation_drift.py --report-dir "$(AI_BRAIN_REPORT_DIR)" --output "$(AI_BRAIN_REPORT_DIR)/implementation-drift_report.json"

implementation-drift: framework-drift

improvement-queue: check-python
	$(PYTHON) tools/run_improvement_queue.py --output "$(AI_BRAIN_REPORT_DIR)/improvement-queue_report.json"

conversation-feedback: check-python
	$(PYTHON) tools/analyze_conversation_feedback.py --project-root "$(TARGET_ROOT)" --output "$(AI_BRAIN_REPORT_DIR)/conversation-feedback_report.json" --patch-brief "$(AI_BRAIN_REPORT_DIR)/conversation-feedback_patch_brief.md" --state "$(AI_BRAIN_DATA_ROOT)/state/conversation_feedback_state.local.json" --force

conversation-feedback-due: check-python
	$(PYTHON) tools/analyze_conversation_feedback.py --project-root "$(TARGET_ROOT)" --output "$(AI_BRAIN_REPORT_DIR)/conversation-feedback_report.json" --patch-brief "$(AI_BRAIN_REPORT_DIR)/conversation-feedback_patch_brief.md" --state "$(AI_BRAIN_DATA_ROOT)/state/conversation_feedback_state.local.json"

harness-check: check-python
	$(PYTHON) tools/validate_harness_quality.py --report-dir "$(AI_BRAIN_REPORT_DIR)" --output "$(AI_BRAIN_REPORT_DIR)/harness-quality_report.json"

team-reliability: check-python
	$(PYTHON) tools/score_team_reliability.py --report-dir "$(AI_BRAIN_REPORT_DIR)" --output "$(AI_BRAIN_REPORT_DIR)/team-reliability_report.json" --history "$(AI_BRAIN_REPORT_DIR)/team-reliability_history.jsonl"

release-gate: check-python
	$(PYTHON) tools/run_release_gate.py --report-dir "$(AI_BRAIN_REPORT_DIR)" --profile "$(AI_BRAIN_PROFILE)" --state "$(AI_BRAIN_STATE)" --output "$(AI_BRAIN_REPORT_DIR)/release-gate_report.json"

report-html: check-python
	$(PYTHON) tools/generate_combined_report_html.py --report-dir "$(AI_BRAIN_REPORT_DIR)" --output "$(AI_BRAIN_REPORT_DIR)/combined_report.html"

maintenance-daily:
	mkdir -p "$(AI_BRAIN_REPORT_DIR)"
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
