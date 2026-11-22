SKILLS_DIR := $(HOME)/.claude/skills
SKILLS := $(notdir $(patsubst %/,%,$(wildcard skills/*/)))

.PHONY: install uninstall test

install:
	@mkdir -p $(SKILLS_DIR)
	@for s in $(SKILLS); do \
	  dst="$(SKILLS_DIR)/$$s"; \
	  if [ -e "$$dst" ] && [ ! -L "$$dst" ]; then \
	    echo "arbiter: ~/.claude/skills/$$s exists and is not a symlink"; exit 1; \
	  fi; \
	  ln -sfn "$(CURDIR)/skills/$$s" "$$dst"; \
	  echo "linked $$dst"; \
	done

uninstall:
	@for l in $(SKILLS_DIR)/*; do \
	  if [ -L "$$l" ]; then \
	    case "$$(readlink "$$l")" in "$(CURDIR)/skills/"*) rm "$$l"; echo "removed $$l";; esac; \
	  fi; \
	done

test:
	uv run pytest -q
