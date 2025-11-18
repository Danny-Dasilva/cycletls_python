"""
URL-Encoded Form Data Tests for CycleTLS Python library.

Based on CycleTLS TypeScript urlencoded tests, these tests verify:
- Basic form submission with application/x-www-form-urlencoded
- Special characters in values (encoding)
- Array/list values
- Nested data structures (if supported)
- Unicode and international characters

All tests use httpbin.org/post endpoint for testing form submissions.
"""

import pytest
import json
from urllib.parse import urlencode
from test_utils import (
    assert_valid_response,
    assert_valid_json_response,
)


class TestBasicURLEncodedForm:
    """Test basic URL-encoded form submissions."""

    def test_basic_url_encoded_form(self, cycletls_client, httpbin_url):
        """Test basic URL-encoded form data with key-value pairs."""
        form_data = {
            "key1": "value1",
            "key2": "value2"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        # Verify the form data was received
        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"
        assert data['form']['key1'] == 'value1', \
            f"Expected key1='value1', got {data['form'].get('key1')}"
        assert data['form']['key2'] == 'value2', \
            f"Expected key2='value2', got {data['form'].get('key2')}"

    def test_simple_login_form(self, cycletls_client, httpbin_url):
        """Test a typical login form submission."""
        form_data = {
            "username": "testuser",
            "password": "testpassword123",
            "remember": "on"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"
        assert data['form']['username'] == 'testuser', "Username should be preserved"
        assert data['form']['password'] == 'testpassword123', "Password should be preserved"
        assert data['form']['remember'] == 'on', "Remember flag should be preserved"

    def test_empty_form_submission(self, cycletls_client, httpbin_url):
        """Test submitting an empty form."""
        form_data = {}

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        # Empty form should result in empty form dict
        assert 'form' in data, "Response should contain 'form' field"


class TestSpecialCharacters:
    """Test URL-encoded forms with special characters."""

    def test_special_characters_encoding(self, cycletls_client, httpbin_url):
        """Test form data with special characters that need URL encoding."""
        form_data = {
            "email": "test+user@example.com",
            "message": "Hello & Welcome!",
            "query": "search=python&filter=active",
            "symbols": "!@#$%^&*()"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify special characters are preserved correctly
        assert data['form']['email'] == form_data['email'], \
            "Email with + sign should be preserved"
        assert data['form']['message'] == form_data['message'], \
            "Message with & should be preserved"
        assert data['form']['query'] == form_data['query'], \
            "Query with special chars should be preserved"

    def test_unicode_characters(self, cycletls_client, httpbin_url):
        """Test form data with Unicode/international characters."""
        form_data = {
            "name": "José García",
            "city": "São Paulo",
            "greeting": "Hello 世界",
            "emoji": "Hello 🌍 World 🚀",
            "cyrillic": "Привет мир",
            "arabic": "مرحبا بالعالم"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify Unicode characters are preserved
        assert data['form']['name'] == form_data['name'], \
            "Name with accents should be preserved"
        assert data['form']['greeting'] == form_data['greeting'], \
            "Greeting with Chinese characters should be preserved"
        assert data['form']['emoji'] == form_data['emoji'], \
            "Emoji should be preserved"

    def test_whitespace_and_newlines(self, cycletls_client, httpbin_url):
        """Test form data with whitespace and newlines."""
        form_data = {
            "text": "Line 1\nLine 2\nLine 3",
            "spaces": "  multiple   spaces  ",
            "tabs": "text\twith\ttabs",
            "mixed": "Text with\n\ttabs and\r\nnewlines"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify whitespace is preserved (may vary based on server handling)
        assert 'text' in data['form'], "Text field should be present"
        assert 'spaces' in data['form'], "Spaces field should be present"

    def test_quotes_and_backslashes(self, cycletls_client, httpbin_url):
        """Test form data with quotes and backslashes."""
        form_data = {
            "single_quote": "It's a test",
            "double_quote": 'He said "hello"',
            "backslash": "path\\to\\file",
            "mixed": 'Test "quotes" and \\ backslashes'
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify quotes and backslashes are preserved
        assert data['form']['single_quote'] == form_data['single_quote'], \
            "Single quotes should be preserved"
        assert data['form']['backslash'] == form_data['backslash'], \
            "Backslashes should be preserved"


class TestArrayValues:
    """Test URL-encoded forms with array/list values."""

    def test_multiple_values_same_key(self, cycletls_client, httpbin_url):
        """Test form data with multiple values for the same key (arrays)."""
        # For multiple values with the same key, use a list of tuples
        # Note: Library doesn't support sequences yet, so we manually encode
        form_pairs = [
            ("colors", "red"),
            ("colors", "green"),
            ("colors", "blue"),
            ("category", "electronics")
        ]

        # Manual encoding needed for sequences (library limitation)
        encoded_data = urlencode(form_pairs)

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body=encoded_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # httpbin might return array values as comma-separated or as last value
        # depending on implementation
        assert 'colors' in data['form'], "Colors field should be present"
        assert 'category' in data['form'], "Category field should be present"

    def test_array_bracket_notation(self, cycletls_client, httpbin_url):
        """Test form data with array bracket notation (items[0], items[1])."""
        form_data = {
            "items[0]": "first",
            "items[1]": "second",
            "items[2]": "third",
            "count": "3"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify array items are present (as separate keys)
        assert 'items[0]' in data['form'], "Array item 0 should be present"
        assert data['form']['items[0]'] == 'first', "Array item 0 value should match"
        assert 'items[1]' in data['form'], "Array item 1 should be present"
        assert data['form']['items[1]'] == 'second', "Array item 1 value should match"


class TestNestedStructures:
    """Test URL-encoded forms with nested data structures."""

    def test_nested_object_notation(self, cycletls_client, httpbin_url):
        """Test form data with nested object notation (user[name], user[email])."""
        form_data = {
            "user[name]": "John Doe",
            "user[email]": "john@example.com",
            "user[age]": "30",
            "address[street]": "123 Main St",
            "address[city]": "New York",
            "address[zip]": "10001"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify nested fields are present (as flat keys)
        assert 'user[name]' in data['form'], "Nested user name should be present"
        assert data['form']['user[name]'] == 'John Doe', "User name should match"
        assert 'user[email]' in data['form'], "Nested user email should be present"
        assert data['form']['user[email]'] == 'john@example.com', "User email should match"
        assert 'address[city]' in data['form'], "Nested address city should be present"

    def test_deeply_nested_notation(self, cycletls_client, httpbin_url):
        """Test form data with deeply nested notation."""
        form_data = {
            "data[user][profile][name]": "Jane Doe",
            "data[user][profile][age]": "25",
            "data[settings][theme]": "dark",
            "data[settings][notifications][email]": "true",
            "data[settings][notifications][sms]": "false"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify deeply nested fields are present
        assert 'data[user][profile][name]' in data['form'], \
            "Deeply nested name should be present"
        assert data['form']['data[user][profile][name]'] == 'Jane Doe', \
            "Deeply nested name should match"


class TestLargeFormData:
    """Test URL-encoded forms with large amounts of data."""

    def test_many_fields(self, cycletls_client, httpbin_url):
        """Test form with many fields."""
        # Create form with 100 fields
        form_data = {f"field_{i}": f"value_{i}" for i in range(100)}

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify a sample of fields
        assert 'field_0' in data['form'], "First field should be present"
        assert 'field_50' in data['form'], "Middle field should be present"
        assert 'field_99' in data['form'], "Last field should be present"
        assert data['form']['field_0'] == 'value_0', "Field value should match"

    def test_long_field_values(self, cycletls_client, httpbin_url):
        """Test form with long field values."""
        # Create form with long text values
        long_text = "Lorem ipsum dolor sit amet. " * 100  # ~2.8KB of text

        form_data = {
            "description": long_text,
            "notes": long_text,
            "title": "Short title"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify long values are preserved
        assert 'description' in data['form'], "Description field should be present"
        assert len(data['form']['description']) > 2000, \
            "Description should be long"
        assert data['form']['title'] == 'Short title', \
            "Title should be preserved"


class TestEdgeCases:
    """Test edge cases in URL-encoded form handling."""

    def test_empty_values(self, cycletls_client, httpbin_url):
        """Test form with empty values."""
        form_data = {
            "field1": "",
            "field2": "value2",
            "field3": "",
            "field4": "value4"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify empty values are handled
        assert 'field1' in data['form'], "Field with empty value should be present"
        assert 'field2' in data['form'], "Field with value should be present"
        assert data['form']['field2'] == 'value2', "Non-empty value should match"

    def test_numeric_values(self, cycletls_client, httpbin_url):
        """Test form with numeric values (sent as strings)."""
        form_data = {
            "age": "25",
            "price": "19.99",
            "quantity": "100",
            "percentage": "75.5"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify numeric values are preserved as strings
        assert data['form']['age'] == '25', "Age should be preserved"
        assert data['form']['price'] == '19.99', "Price should be preserved"
        assert data['form']['quantity'] == '100', "Quantity should be preserved"

    def test_boolean_like_values(self, cycletls_client, httpbin_url):
        """Test form with boolean-like string values."""
        form_data = {
            "active": "true",
            "enabled": "false",
            "checked": "on",
            "unchecked": "off",
            "yes_field": "yes",
            "no_field": "no"
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            data=form_data
        )

        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)
        assert 'form' in data, "Response should contain 'form' field"

        # Verify boolean-like values are preserved as strings
        assert data['form']['active'] == 'true', "Boolean string should be preserved"
        assert data['form']['checked'] == 'on', "On value should be preserved"
        assert data['form']['unchecked'] == 'off', "Off value should be preserved"
