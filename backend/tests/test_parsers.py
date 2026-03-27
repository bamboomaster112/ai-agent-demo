"""Tests for the response parser."""

from app.agent.parsers import parse_migration_response


def test_extract_yaml_blocks():
    text = """Here's your GitHub Actions workflow:

```yaml
# .github/workflows/ci.yml
name: CI
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: mvn clean package
```

WARNING: The deploy step uses a custom script that needs manual configuration.
NOTE: Consider adding caching for Maven dependencies.
"""
    result = parse_migration_response(text)
    assert len(result.yaml_blocks) == 1
    assert result.yaml_blocks[0].filename == ".github/workflows/ci.yml"
    assert "name: CI" in result.yaml_blocks[0].content
    assert len(result.warnings) == 1
    assert "deploy" in result.warnings[0].lower()
    assert len(result.notes) == 1
    assert "caching" in result.notes[0].lower()


def test_multiple_yaml_blocks():
    text = """You'll need two workflow files:

```yaml
# .github/workflows/ci.yml
name: CI
on: push
```

```yaml
# .github/workflows/deploy.yml
name: Deploy
on: workflow_dispatch
```
"""
    result = parse_migration_response(text)
    assert len(result.yaml_blocks) == 2
    assert result.yaml_blocks[0].filename == ".github/workflows/ci.yml"
    assert result.yaml_blocks[1].filename == ".github/workflows/deploy.yml"


def test_no_yaml_blocks():
    text = "I need more information about your pipeline. What triggers should it use?"
    result = parse_migration_response(text)
    assert len(result.yaml_blocks) == 0
    assert len(result.warnings) == 0
    assert len(result.notes) == 0
    assert result.raw_text == text
