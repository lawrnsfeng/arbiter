OMP_SKILLS := $(HOME)/.omp/agent/skills
CLAUDE_SKILLS := $(HOME)/.claude/skills
SKILLS := $(notdir $(patsubst %/,%,$(wildcard skills/*/)))

.PHONY: install install-claude uninstall test check

# the `arbiter` command on PATH (editable: it runs this checkout) plus the skills for omp
install:
	uv tool install --force --editable "$(CURDIR)"
	@$(MAKE) --no-print-directory link DIR="$(OMP_SKILLS)"

# also expose the skills to Claude Code (omp reads ~/.claude/skills too when skills.enableClaudeUser is on)
install-claude:
	@$(MAKE) --no-print-directory link DIR="$(CLAUDE_SKILLS)"

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

uninstall:
	-uv tool uninstall arbiter
	@for l in $(OMP_SKILLS)/* $(CLAUDE_SKILLS)/*; do \
	  if [ -L "$$l" ]; then \
	    case "$$(readlink "$$l")" in "$(CURDIR)/skills/"*) rm "$$l"; echo "removed $$l";; esac; \
	  fi; \
	done

test:
	uv run pytest -q

check:
	uv run ruff check arbiter tests
	uv run ruff format --check arbiter tests
	uv run mypy
	uv run pytest -q
