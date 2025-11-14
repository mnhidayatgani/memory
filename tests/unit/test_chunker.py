"""Unit tests for file chunking utilities."""

import pytest

from hmc.chunker import chunk_file_content


class TestChunkFileContent:
    """Unit tests for chunk_file_content function."""

    def test_simple_content_single_chunk(self):
        """Test that small content returns single chunk."""
        content = "This is a short piece of text."
        
        chunks = chunk_file_content(content, max_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0]["content"] == content
        assert chunks[0]["line_range"] == (1, 1)

    def test_paragraph_aware_splitting(self):
        """Test that splitting respects paragraph boundaries."""
        content = """First paragraph.

Second paragraph with more text.

Third paragraph here."""
        
        chunks = chunk_file_content(content, max_size=50)
        
        # Should split at paragraph boundaries
        assert len(chunks) >= 2
        assert all("content" in chunk for chunk in chunks)
        assert all("line_range" in chunk for chunk in chunks)

    def test_line_range_tracking(self):
        """Test that line ranges are correctly tracked."""
        content = """Line 1
Line 2
Line 3
Line 4
Line 5"""
        
        chunks = chunk_file_content(content, max_size=20)
        
        # Verify line ranges are present
        for chunk in chunks:
            assert "line_range" in chunk
            assert "-" in chunk["line_range"]
            
            # Parse line range
            start, end = map(int, chunk["line_range"].split("-"))
            assert start >= 1
            assert end >= start

    def test_oversized_section_splitting(self):
        """Test that oversized sections are split by character boundaries."""
        # Single long line without paragraph breaks
        content = "A" * 5000  # Much larger than max_size
        
        chunks = chunk_file_content(content, max_size=2000)
        
        # Should be split into multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should be <= max_size
        for chunk in chunks:
            assert len(chunk["content"]) <= 2000

    def test_max_size_parameter(self):
        """Test that max_size parameter is respected."""
        content = "x " * 1000  # 2000 characters
        
        chunks_small = chunk_file_content(content, max_size=500)
        chunks_large = chunk_file_content(content, max_size=1500)
        
        # Smaller max_size should produce more chunks
        assert len(chunks_small) > len(chunks_large)

    def test_empty_content(self):
        """Test handling of empty content."""
        content = ""
        
        chunks = chunk_file_content(content, max_size=2000)
        
        # Should return empty list for empty content
        assert len(chunks) == 0

    def test_whitespace_only_content(self):
        """Test handling of whitespace-only content."""
        content = "   \n\n   \t\t   \n"
        
        chunks = chunk_file_content(content, max_size=2000)
        
        assert len(chunks) >= 1
        assert all("content" in chunk for chunk in chunks)

    def test_multiline_paragraphs(self):
        """Test chunking with multi-line paragraphs."""
        content = """This is the first paragraph.
It spans multiple lines.
But it's still one paragraph.

This is the second paragraph.
It also has multiple lines.

Third paragraph."""
        
        chunks = chunk_file_content(content, max_size=100)
        
        # Verify all content is preserved
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content

    def test_code_with_functions(self):
        """Test chunking Python code with functions."""
        content = """def function1():
    \"\"\"First function.\"\"\"
    return 1

def function2():
    \"\"\"Second function.\"\"\"
    return 2

def function3():
    \"\"\"Third function.\"\"\"
    return 3"""
        
        chunks = chunk_file_content(content, max_size=100)
        
        # Should split between functions
        assert len(chunks) > 1
        assert all("content" in chunk for chunk in chunks)

    def test_preserves_newlines(self):
        """Test that newlines are preserved in chunks."""
        content = "Line 1\n\nLine 2\n\n\nLine 3"
        
        chunks = chunk_file_content(content, max_size=1000)
        
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content

    def test_chunk_metadata_structure(self):
        """Test that each chunk has required metadata."""
        content = "Test content\n\nMore content"
        
        chunks = chunk_file_content(content, max_size=1000)
        
        for chunk in chunks:
            assert isinstance(chunk, dict)
            assert "content" in chunk
            assert "line_range" in chunk
            assert isinstance(chunk["content"], str)
            assert isinstance(chunk["line_range"], tuple)

    def test_sequential_line_ranges(self):
        """Test that line ranges are sequential and non-overlapping."""
        content = "\n".join([f"Line {i}" for i in range(1, 101)])
        
        chunks = chunk_file_content(content, max_size=200)
        
        last_end = 0
        for chunk in chunks:
            start, end = map(int, chunk["line_range"].split("-"))
            
            # Start should be after previous end
            if last_end > 0:
                assert start == last_end + 1 or start == last_end
            
            last_end = end

    def test_single_long_line(self):
        """Test handling of single very long line."""
        content = "a" * 10000
        
        chunks = chunk_file_content(content, max_size=2000)
        
        # Should be split into multiple chunks
        assert len(chunks) > 1
        
        # Reconstruct and verify
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content

    def test_mixed_line_lengths(self):
        """Test content with mixed short and long lines."""
        content = """Short line.
This is a much longer line that contains significantly more text than the previous one.
Another short line.
Yet another very long line with lots of text that goes on and on and on.
Final short line."""
        
        chunks = chunk_file_content(content, max_size=100)
        
        # Verify integrity
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content

    def test_markdown_content(self):
        """Test chunking Markdown document."""
        content = """# Header 1

This is a paragraph under header 1.

## Header 2

This is a paragraph under header 2.

### Header 3

Final paragraph."""
        
        chunks = chunk_file_content(content, max_size=80)
        
        # Verify all content preserved
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content

    def test_default_max_size(self):
        """Test that default max_size of 2000 is used."""
        content = "x" * 3000
        
        # Call without max_size parameter (should use default 2000)
        chunks = chunk_file_content(content)
        
        # Should be split into at least 2 chunks
        assert len(chunks) >= 2

    def test_special_characters(self):
        """Test handling of special characters."""
        content = """Line with emoji: 😀
Line with unicode: Ü ñ ö
Line with symbols: @#$%^&*()
Line with quotes: "double" and 'single'"""
        
        chunks = chunk_file_content(content, max_size=1000)
        
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content

    def test_very_small_max_size(self):
        """Test behavior with very small max_size."""
        content = "This is a test."
        
        chunks = chunk_file_content(content, max_size=5)
        
        # Should still produce valid chunks
        assert len(chunks) > 1
        assert all("content" in chunk for chunk in chunks)
        
        # Reconstruct
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content

    def test_exact_max_size_boundary(self):
        """Test content exactly at max_size boundary."""
        content = "a" * 2000
        
        chunks = chunk_file_content(content, max_size=2000)
        
        # Should fit in one chunk
        assert len(chunks) == 1
        assert chunks[0]["content"] == content

    def test_just_over_max_size(self):
        """Test content just over max_size."""
        content = "a" * 2001
        
        chunks = chunk_file_content(content, max_size=2000)
        
        # Should be split into 2 chunks
        assert len(chunks) >= 2

    def test_multiple_empty_lines(self):
        """Test handling of multiple consecutive empty lines."""
        content = "Line 1\n\n\n\n\nLine 2"
        
        chunks = chunk_file_content(content, max_size=1000)
        
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content

    def test_tabs_and_spaces(self):
        """Test preservation of tabs and spaces."""
        content = "Line with\ttabs\nLine with    spaces\n\tIndented line"
        
        chunks = chunk_file_content(content, max_size=1000)
        
        reconstructed = "".join(chunk["content"] for chunk in chunks)
        assert reconstructed == content
