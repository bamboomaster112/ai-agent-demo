"""Context-aware chunking strategies for CI/CD pipeline configurations."""

import re
from abc import ABC, abstractmethod

import tiktoken


class Chunk:
    def __init__(self, content: str, metadata: dict | None = None, token_count: int = 0):
        self.content = content
        self.metadata = metadata or {}
        self.token_count = token_count


class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, content: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[Chunk]:
        ...


class JenkinsGroovyChunker(ChunkingStrategy):
    """Splits Jenkins pipelines on stage boundaries, keeping pipeline-level context."""

    def chunk(self, content: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[Chunk]:
        enc = tiktoken.get_encoding("cl100k_base")
        chunks = []

        # Extract pipeline-level context header (agent, environment, options)
        header_match = re.search(
            r"(pipeline\s*\{.*?(?=stages\s*\{))", content, re.DOTALL
        )
        header = header_match.group(1).strip() if header_match else ""

        # Split on stages
        stage_pattern = re.compile(
            r"stage\s*\(\s*['\"](.+?)['\"]\s*\)\s*\{", re.DOTALL
        )
        stage_positions = [(m.start(), m.group(1)) for m in stage_pattern.finditer(content)]

        if not stage_positions:
            # No stages found, fall back to token-based chunking
            return FallbackChunker().chunk(content, chunk_size, chunk_overlap)

        for i, (pos, stage_name) in enumerate(stage_positions):
            # Determine stage end
            end = stage_positions[i + 1][0] if i + 1 < len(stage_positions) else len(content)
            stage_content = content[pos:end].strip()

            # Prepend header for context
            full_chunk = f"{header}\n// Stage: {stage_name}\n{stage_content}" if header else stage_content
            tokens = len(enc.encode(full_chunk))

            if tokens <= chunk_size:
                chunks.append(Chunk(
                    content=full_chunk,
                    metadata={"stage_name": stage_name, "type": "stage"},
                    token_count=tokens,
                ))
            else:
                # Stage too large, split into sub-chunks
                sub_chunks = FallbackChunker().chunk(full_chunk, chunk_size, chunk_overlap)
                for j, sc in enumerate(sub_chunks):
                    sc.metadata.update({"stage_name": stage_name, "type": "stage_part", "part": j})
                chunks.extend(sub_chunks)

        # Post block
        post_match = re.search(r"(post\s*\{.*)", content, re.DOTALL)
        if post_match:
            post_content = post_match.group(1).strip()
            tokens = len(enc.encode(post_content))
            chunks.append(Chunk(
                content=post_content,
                metadata={"type": "post_block"},
                token_count=tokens,
            ))

        return chunks


class TeamCityKotlinChunker(ChunkingStrategy):
    """Splits TeamCity Kotlin DSL on buildType / vcsRoot / object boundaries."""

    def chunk(self, content: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[Chunk]:
        enc = tiktoken.get_encoding("cl100k_base")
        chunks = []

        # Extract project-level header
        header_match = re.search(r"(project\s*\{.*?(?=buildType|object\s))", content, re.DOTALL)
        header = header_match.group(1).strip() if header_match else ""

        # Split on buildType / object declarations
        block_pattern = re.compile(
            r"((?:object\s+\w+\s*:.*?\{|buildType\s*\{|vcsRoot\s*\().*?)(?=(?:object\s+\w+|buildType\s*\{|vcsRoot\s*\(|\Z))",
            re.DOTALL,
        )

        blocks = block_pattern.findall(content)

        if not blocks:
            return FallbackChunker().chunk(content, chunk_size, chunk_overlap)

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            full_chunk = f"{header}\n{block}" if header else block
            tokens = len(enc.encode(full_chunk))

            # Detect block name
            name_match = re.search(r"object\s+(\w+)", block)
            block_name = name_match.group(1) if name_match else "buildType"

            if tokens <= chunk_size:
                chunks.append(Chunk(
                    content=full_chunk,
                    metadata={"block_name": block_name, "type": "build_type"},
                    token_count=tokens,
                ))
            else:
                sub_chunks = FallbackChunker().chunk(full_chunk, chunk_size, chunk_overlap)
                for sc in sub_chunks:
                    sc.metadata.update({"block_name": block_name, "type": "build_type_part"})
                chunks.extend(sub_chunks)

        return chunks


class TeamCityXMLChunker(ChunkingStrategy):
    """Splits TeamCity XML configs on element boundaries."""

    def chunk(self, content: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[Chunk]:
        enc = tiktoken.get_encoding("cl100k_base")
        chunks = []

        # Split on major XML elements
        element_pattern = re.compile(
            r"(<(?:build-type|vcs-root|build-runner|step)\b[^>]*>.*?</(?:build-type|vcs-root|build-runner|step)>)",
            re.DOTALL,
        )

        elements = element_pattern.findall(content)

        if not elements:
            return FallbackChunker().chunk(content, chunk_size, chunk_overlap)

        for elem in elements:
            tokens = len(enc.encode(elem))
            tag_match = re.search(r"<(\w[\w-]*)", elem)
            tag_name = tag_match.group(1) if tag_match else "element"

            if tokens <= chunk_size:
                chunks.append(Chunk(
                    content=elem,
                    metadata={"element": tag_name, "type": "xml_element"},
                    token_count=tokens,
                ))
            else:
                sub_chunks = FallbackChunker().chunk(elem, chunk_size, chunk_overlap)
                for sc in sub_chunks:
                    sc.metadata.update({"element": tag_name, "type": "xml_part"})
                chunks.extend(sub_chunks)

        return chunks


class MarkdownDocChunker(ChunkingStrategy):
    """Splits documentation on heading boundaries."""

    def chunk(self, content: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[Chunk]:
        enc = tiktoken.get_encoding("cl100k_base")
        chunks = []

        # Split on headings
        sections = re.split(r"\n(?=#{1,3}\s)", content)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            tokens = len(enc.encode(section))
            heading_match = re.match(r"^(#{1,3})\s+(.+)", section)
            heading = heading_match.group(2) if heading_match else ""

            if tokens <= chunk_size:
                chunks.append(Chunk(
                    content=section,
                    metadata={"heading": heading, "type": "doc_section"},
                    token_count=tokens,
                ))
            else:
                sub_chunks = FallbackChunker().chunk(section, chunk_size, chunk_overlap)
                for sc in sub_chunks:
                    sc.metadata.update({"heading": heading, "type": "doc_section_part"})
                chunks.extend(sub_chunks)

        return chunks


class FallbackChunker(ChunkingStrategy):
    """Token-based sliding window with overlap. Used as fallback."""

    def chunk(self, content: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[Chunk]:
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(content)
        chunks = []

        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = enc.decode(chunk_tokens)

            chunks.append(Chunk(
                content=chunk_text,
                metadata={"type": "token_window", "start_token": start},
                token_count=len(chunk_tokens),
            ))

            start += chunk_size - chunk_overlap

        return chunks


def get_chunker(source_format: str | None = None, doc_type: str | None = None) -> ChunkingStrategy:
    """Factory: return the appropriate chunker based on format or doc type."""
    if source_format == "groovy":
        return JenkinsGroovyChunker()
    elif source_format == "kotlin_dsl":
        return TeamCityKotlinChunker()
    elif source_format == "xml":
        return TeamCityXMLChunker()
    elif doc_type in ("reference_doc", "actions_doc"):
        return MarkdownDocChunker()
    else:
        return FallbackChunker()
