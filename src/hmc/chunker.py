"""File chunking utilities for semantic embedding.

This module provides functions to split file content into manageable chunks
for semantic embedding while preserving context and tracking source locations.
"""


def chunk_file_content(
    content: str, max_size: int = 2000
) -> list[dict[str, str | tuple[int, int]]]:
    """Split file content into chunks suitable for embedding.

    Uses paragraph-aware splitting to maintain semantic coherence.
    Tracks line ranges for source attribution.

    Args:
        content: Text content to chunk
        max_size: Maximum characters per chunk (default: 2000)

    Returns:
        List of chunk dictionaries, each containing:
            - "content": The chunk text
            - "line_range": Tuple of (start_line, end_line) (1-indexed)

    Example:
        >>> content = "Line 1\\n\\nLine 3\\n\\nLine 5"
        >>> chunks = chunk_file_content(content, max_size=10)
        >>> len(chunks) > 0
        True
        >>> "content" in chunks[0] and "line_range" in chunks[0]
        True
    """
    if not content:
        return []

    lines = content.split("\n")
    chunks: list[dict[str, str | tuple[int, int]]] = []

    current_chunk: list[str] = []
    current_size = 0
    chunk_start_line = 1
    current_line = 1

    for line in lines:
        line_len = len(line) + 1  # +1 for newline

        # If adding this line would exceed max_size
        if current_size + line_len > max_size and current_chunk:
            # Save current chunk
            chunk_content = "\n".join(current_chunk)
            chunks.append(
                {
                    "content": chunk_content,
                    "line_range": (chunk_start_line, current_line - 1),
                }
            )

            # Start new chunk
            current_chunk = [line]
            current_size = line_len
            chunk_start_line = current_line
        else:
            # Add line to current chunk
            current_chunk.append(line)
            current_size += line_len

        current_line += 1

    # Save remaining chunk if any
    if current_chunk:
        chunk_content = "\n".join(current_chunk)
        chunks.append(
            {
                "content": chunk_content,
                "line_range": (chunk_start_line, current_line - 1),
            }
        )

    # Handle case where a single line is larger than max_size
    # Split it by character boundaries
    final_chunks: list[dict[str, str | tuple[int, int]]] = []
    for chunk in chunks:
        content_str = chunk["content"]
        if isinstance(content_str, str) and len(content_str) > max_size:
            # Split oversized chunk by characters
            start_line, end_line = chunk["line_range"]  # type: ignore
            pos = 0
            while pos < len(content_str):
                piece = content_str[pos : pos + max_size]
                final_chunks.append(
                    {
                        "content": piece,
                        "line_range": (start_line, end_line),
                    }
                )
                pos += max_size
        else:
            final_chunks.append(chunk)

    return final_chunks
