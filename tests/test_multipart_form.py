"""
Multipart Form Data Tests for CycleTLS Python library.

Based on CycleTLS TypeScript multipartFormData tests, these tests verify:
- File upload with multipart/form-data
- Multiple files upload
- Mixed form fields and files
- Large file handling
- Data integrity for file uploads

All tests use httpbin.org/post endpoint for testing multipart form data.
"""

import pytest
import os
import tempfile
import hashlib
from test_utils import (
    assert_valid_response,
    assert_valid_json_response,
)


class TestMultipartFormData:
    """Test basic multipart form data submissions."""

    def test_basic_multipart_form_data(self, cycletls_client, httpbin_url):
        """Test basic multipart form data with key-value pairs."""
        # Note: Python CycleTLS should support multipart form data
        # This test assumes the library has form_data or similar parameter
        form_data = {
            "key1": "value1",
            "key2": "value2"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            form_data=form_data
        )

        assert_valid_response(response, expected_status=200)

        # Verify the form data was received
        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"
        assert data['form']['key1'] == 'value1', \
            f"Expected key1='value1', got {data['form'].get('key1')}"
        assert data['form']['key2'] == 'value2', \
            f"Expected key2='value2', got {data['form'].get('key2')}"

    def test_multipart_with_special_characters(self, cycletls_client, httpbin_url):
        """Test multipart form data with special characters in values."""
        form_data = {
            "name": "John Doe",
            "email": "test+special@example.com",
            "message": "Hello! & Welcome <> to \"testing\" 'forms'",
            "unicode": "Hello 世界 🌍"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            form_data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"
        assert data['form']['email'] == form_data['email'], \
            "Email with special chars should be preserved"
        assert data['form']['unicode'] == form_data['unicode'], \
            "Unicode characters should be preserved"


class TestFileUpload:
    """Test file upload functionality with multipart/form-data."""

    def test_single_file_upload(self, cycletls_client, httpbin_url):
        """Test uploading a single file with multipart/form-data."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_content = "This is test file content for multipart upload.\nIt contains multiple lines."
            f.write(test_content)
            temp_file_path = f.name

        try:
            # Upload the file
            with open(temp_file_path, 'rb') as f:
                files = {
                    'file': ('test.txt', f, 'text/plain')
                }

                response = cycletls_client.post(
                    f"{httpbin_url}/post",
                    files=files
                )

            assert_valid_response(response, expected_status=200)

            # Verify the file was received
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"
            assert 'file' in data['files'], "Uploaded file should be present"
            assert test_content in data['files']['file'], \
                "File content should be preserved"

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_file_upload_with_form_fields(self, cycletls_client, httpbin_url):
        """Test uploading file along with regular form fields."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_content = "File content for mixed upload test"
            f.write(test_content)
            temp_file_path = f.name

        try:
            # Upload file with form fields
            with open(temp_file_path, 'rb') as f:
                files = {
                    'file': ('document.txt', f, 'text/plain')
                }
                form_data = {
                    'title': 'Test Document',
                    'description': 'A test file upload',
                    'category': 'testing'
                }

                response = cycletls_client.post(
                    f"{httpbin_url}/post",
                    files=files,
                    form_data=form_data
                )

            assert_valid_response(response, expected_status=200)

            # Verify both file and form data were received
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"
            assert 'form' in data, "Response should contain 'form' field"

            # Check form fields
            assert data['form']['title'] == 'Test Document', \
                "Form field 'title' should be preserved"
            assert data['form']['category'] == 'testing', \
                "Form field 'category' should be preserved"

            # Check file
            assert 'file' in data['files'], "Uploaded file should be present"
            assert test_content in data['files']['file'], \
                "File content should be preserved"

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_multiple_files_upload(self, cycletls_client, httpbin_url):
        """Test uploading multiple files simultaneously."""
        # Create multiple temporary test files
        temp_files = []
        file_contents = {
            'file1.txt': 'Content of first file',
            'file2.txt': 'Content of second file',
            'file3.txt': 'Content of third file'
        }

        try:
            # Create temp files
            for filename, content in file_contents.items():
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    f.write(content)
                    temp_files.append((filename, f.name, content))

            # Upload all files
            files = {}
            for idx, (orig_name, temp_path, content) in enumerate(temp_files):
                with open(temp_path, 'rb') as f:
                    files[f'file{idx+1}'] = (orig_name, f.read(), 'text/plain')

            response = cycletls_client.post(
                f"{httpbin_url}/post",
                files=files
            )

            assert_valid_response(response, expected_status=200)

            # Verify all files were received
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"

            # Check each file
            for idx, (orig_name, temp_path, content) in enumerate(temp_files):
                field_name = f'file{idx+1}'
                assert field_name in data['files'], \
                    f"File '{field_name}' should be present in response"
                assert content in data['files'][field_name], \
                    f"Content of '{field_name}' should be preserved"

        finally:
            # Clean up all temp files
            for _, temp_path, _ in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_binary_file_upload(self, cycletls_client, httpbin_url):
        """Test uploading binary file (simulated image)."""
        # Create a temporary binary file (fake JPEG)
        fake_jpeg_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xD9
        ])

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(fake_jpeg_data)
            temp_file_path = f.name

        try:
            # Upload binary file
            with open(temp_file_path, 'rb') as f:
                files = {
                    'image': ('photo.jpg', f, 'image/jpeg')
                }

                response = cycletls_client.post(
                    f"{httpbin_url}/post",
                    files=files
                )

            assert_valid_response(response, expected_status=200)

            # Verify file was received
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"
            assert 'image' in data['files'], "Uploaded image should be present"

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class TestLargeFileUpload:
    """Test handling of large files in multipart uploads."""

    def test_large_text_file_upload(self, cycletls_client, httpbin_url):
        """Test uploading a larger text file (several KB)."""
        # Create a large text file (100KB)
        large_content = "This is a line of text that will be repeated many times.\n" * 2000
        content_hash = hashlib.md5(large_content.encode()).hexdigest()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(large_content)
            temp_file_path = f.name
            file_size = os.path.getsize(temp_file_path)

        try:
            assert file_size > 50000, \
                f"Test file should be large (>50KB), got {file_size} bytes"

            # Upload large file
            with open(temp_file_path, 'rb') as f:
                files = {
                    'largefile': ('large.txt', f, 'text/plain')
                }

                response = cycletls_client.post(
                    f"{httpbin_url}/post",
                    files=files
                )

            assert_valid_response(response, expected_status=200)

            # Verify file was received
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"
            assert 'largefile' in data['files'], "Large file should be present"

            # Verify content integrity (at least check size)
            received_content = data['files']['largefile']
            assert len(received_content) > 50000, \
                f"Received content should be large, got {len(received_content)} chars"

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_large_binary_file_upload(self, cycletls_client, httpbin_url):
        """Test uploading a large binary file."""
        # Create a large binary file (200KB of pseudo-random data)
        binary_pattern = bytes(range(256)) * 800  # 200KB
        content_hash = hashlib.md5(binary_pattern).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(binary_pattern)
            temp_file_path = f.name
            file_size = os.path.getsize(temp_file_path)

        try:
            assert file_size > 100000, \
                f"Test file should be large (>100KB), got {file_size} bytes"

            # Upload large binary file
            with open(temp_file_path, 'rb') as f:
                files = {
                    'binaryfile': ('data.bin', f, 'application/octet-stream')
                }

                response = cycletls_client.post(
                    f"{httpbin_url}/post",
                    files=files
                )

            assert_valid_response(response, expected_status=200)

            # Verify file was received
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"
            assert 'binaryfile' in data['files'], "Binary file should be present"

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class TestMultipartEdgeCases:
    """Test edge cases in multipart form data handling."""

    def test_empty_file_upload(self, cycletls_client, httpbin_url):
        """Test uploading an empty file."""
        # Create an empty file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            temp_file_path = f.name

        try:
            # Upload empty file
            with open(temp_file_path, 'rb') as f:
                files = {
                    'emptyfile': ('empty.txt', f, 'text/plain')
                }

                response = cycletls_client.post(
                    f"{httpbin_url}/post",
                    files=files
                )

            assert_valid_response(response, expected_status=200)

            # Verify file was received (even if empty)
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_filename_with_special_characters(self, cycletls_client, httpbin_url):
        """Test uploading file with special characters in filename."""
        # Create a test file with special chars in name
        test_content = "File with special name"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_content)
            temp_file_path = f.name

        try:
            # Upload with special filename
            with open(temp_file_path, 'rb') as f:
                files = {
                    'file': ('test file (2024) [v2].txt', f, 'text/plain')
                }

                response = cycletls_client.post(
                    f"{httpbin_url}/post",
                    files=files
                )

            assert_valid_response(response, expected_status=200)

            # Verify file was received
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"
            assert 'file' in data['files'], "File should be present"

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_mixed_multiple_files_and_fields(self, cycletls_client, httpbin_url):
        """Test complex multipart with multiple files and multiple fields."""
        # Create two test files
        file1_content = "First file content"
        file2_content = "Second file content"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f1:
            f1.write(file1_content)
            temp_file1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f2:
            f2.write(file2_content)
            temp_file2 = f2.name

        try:
            # Upload with multiple files and fields
            with open(temp_file1, 'rb') as f1, open(temp_file2, 'rb') as f2:
                files = {
                    'document': ('doc1.txt', f1, 'text/plain'),
                    'attachment': ('doc2.txt', f2, 'text/plain')
                }
                form_data = {
                    'author': 'Test User',
                    'version': '1.0',
                    'category': 'documentation',
                    'tags': 'test,multipart,upload'
                }

                response = cycletls_client.post(
                    f"{httpbin_url}/post",
                    files=files,
                    form_data=form_data
                )

            assert_valid_response(response, expected_status=200)

            # Verify everything was received
            data = assert_valid_json_response(response)
            assert 'files' in data, "Response should contain 'files' field"
            assert 'form' in data, "Response should contain 'form' field"

            # Check files
            assert 'document' in data['files'], "First file should be present"
            assert 'attachment' in data['files'], "Second file should be present"

            # Check form fields
            assert data['form']['author'] == 'Test User', "Author field should be preserved"
            assert data['form']['version'] == '1.0', "Version field should be preserved"

        finally:
            # Clean up
            if os.path.exists(temp_file1):
                os.unlink(temp_file1)
            if os.path.exists(temp_file2):
                os.unlink(temp_file2)
