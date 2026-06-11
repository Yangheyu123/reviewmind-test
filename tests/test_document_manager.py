"""
Tests for document manager — partial coverage only.
🟡 LOW: Only tests happy path, no edge cases, no error handling tests.
"""
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from document_manager import save_document, list_documents, delete_document


def setup_module():
    """Create temp upload dir for tests."""
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'uploads'), exist_ok=True)


def test_save_document():
    """Test basic document save."""
    result = save_document("test.txt", b"hello world")
    assert result['filename'] == "test.txt"
    assert result['size'] == 11


def test_list_documents():
    """Test document listing."""
    docs = list_documents()
    assert isinstance(docs, list)


def test_delete_document():
    """Test document deletion."""
    result = save_document("to_delete.txt", b"delete me")
    assert delete_document(result['id']) is True


# 🟡 LOW: Missing test coverage for:
#   - Path traversal in save_document (e.g., filename="../../etc/passwd")
#   - Command injection in process_document
#   - Encrypt/decrypt roundtrip
#   - SQL injection in search_documents
#   - Large file handling in read_document
#   - Empty/invalid inputs
#   - Concurrent access
#   - get_document_stats accuracy
#   - Boundary conditions (empty filename, null bytes, unicode)
