OMP_SKILLS := $(HOME)/.omp/agent/skills
CLAUDE_SKILLS := $(HOME)/.claude/skills
SKILLS := $(notdir $(patsubst %/,%,$(wildcard skills/*/)))
OMP_AGENTS := $(HOME)/.omp/agent/agents
CLAUDE_AGENTS := $(HOME)/.claude/agents
AGENTS := $(notdir $(wildcard agents/*.md))

.PHONY: install install-claude uninstall test check link-agents

# the `arbiter` command on PATH (editable: it runs this checkout) plus the skills for omp
install:
	uv tool install --force --editable "$(CURDIR)"
	@$(MAKE) --no-print-directory link DIR="$(OMP_SKILLS)"
	@$(MAKE) --no-print-directory link-agents DIR="$(OMP_AGENTS)"

# also expose the skills to Claude Code (omp reads ~/.claude/skills too when skills.enableClaudeUser is on)
install-claude:
	@$(MAKE) --no-print-directory link DIR="$(CLAUDE_SKILLS)"
	@$(MAKE) --no-print-directory link-agents DIR="$(CLAUDE_AGENTS)"

link:
	@mkdir -p "$(DIR)"
	@for s in $(SKILLS); do \
	  dst="$(DIR)/$$s"; \
	  if [ -e "$$dst" ] && [ ! -L "$$dst" ]; then \
	    echo "arbiter: $$dst exists and is not a symlink"; exit 1; \
	  fi; \
	  ln -sfn "$(CURDIR)/skills/$$s" "$$dst"; \
	  echo "linked $$dst"; \
	done

link-agents:
	@mkdir -p "$(DIR)"
	@for a in $(AGENTS); do \
	  dst="$(DIR)/$$a"; \
	  if [ -e "$$dst" ] && [ ! -L "$$dst" ]; then \
	    echo "arbiter: $$dst exists and is not a symlink"; exit 1; \
	  fi; \
	  ln -sfn "$(CURDIR)/agents/$$a" "$$dst"; \
	  echo "linked $$dst"; \
	done

uninstall:
	-uv tool uninstall arbiter
	@for l in $(OMP_SKILLS)/* $(CLAUDE_SKILLS)/* $(OMP_AGENTS)/* $(CLAUDE_AGENTS)/*; do \
	  if [ -L "$$l" ]; then \
	    case "$$(readlink "$$l")" in "$(CURDIR)/skills/"*|"$(CURDIR)/agents/"*) rm "$$l"; echo "removed $$l";; esac; \
	  fi; \
	done

test:
	uv run pytest -q

check:
	uv run ruff check arbiter tests
	uv run ruff format --check arbiter tests
	uv run mypy
	uv run pytest -q
