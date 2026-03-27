"""Parse Claude's response to extract YAML blocks, warnings, and notes."""

import re
from pydantic import BaseModel


class YamlBlock(BaseModel):
    filename: str
    content: str


class MigrationResult(BaseModel):
    raw_text: str
    yaml_blocks: list[YamlBlock]
    warnings: list[str]
    notes: list[str]


# Regex for fenced YAML blocks
YAML_FENCE_RE = re.compile(
    r"```(?:yaml|yml)\s*\n(.*?)```",
    re.DOTALL,
)

# Regex for filename comments (e.g., "# .github/workflows/ci.yml" before or inside a YAML block)
FILENAME_RE = re.compile(
    r"#\s*(\.github/workflows/[\w\-./]+\.ya?ml)",
)

WARNING_RE = re.compile(r"^WARNING:\s*(.+)$", re.MULTILINE)
NOTE_RE = re.compile(r"^NOTE:\s*(.+)$", re.MULTILINE)


def parse_migration_response(text: str) -> MigrationResult:
    """Parse the AI response into structured components."""
    # Extract YAML blocks
    yaml_blocks = []
    for i, match in enumerate(YAML_FENCE_RE.finditer(text)):
        yaml_content = match.group(1).strip()

        # Try to find a filename in the YAML content or just before it
        filename_match = FILENAME_RE.search(yaml_content)
        if filename_match:
            filename = filename_match.group(1)
        else:
            # Check text just before this block
            pre_text = text[max(0, match.start() - 200):match.start()]
            filename_match = FILENAME_RE.search(pre_text)
            if filename_match:
                filename = filename_match.group(1)
            else:
                filename = f".github/workflows/ci{'_' + str(i + 1) if i > 0 else ''}.yml"

        yaml_blocks.append(YamlBlock(filename=filename, content=yaml_content))

    # Extract warnings
    warnings = [m.group(1).strip() for m in WARNING_RE.finditer(text)]

    # Extract notes
    notes = [m.group(1).strip() for m in NOTE_RE.finditer(text)]

    return MigrationResult(
        raw_text=text,
        yaml_blocks=yaml_blocks,
        warnings=warnings,
        notes=notes,
    )
