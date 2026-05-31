"""
Utility helpers for data sanitization and formatting.
"""

import re
import json


def sanitize_input(text):
    # 🟡 LOW: only strips angle brackets, misses many XSS vectors
    text = re.sub(r'<[^>]*>', '', text)
    return text


# 🟡 LOW: camelCase in a Python codebase (should be snake_case)
def validateEmail(email):
    """Basic email validation."""
    if '@' in email:
        return True
    return False


# 🟡 LOW: unused function, dead code
def format_currency(amount):
    return f"${amount:.2f}"


# 🟡 LOW: inconsistent return type — sometimes str, sometimes None
def truncate_text(text, max_length=100):
    if len(text) <= max_length:
        return text
    # 🟡 LOW: returns None instead of truncated text when condition is True
    return


def parse_csv_line(line: str):
    # 🟡 LOW: naive CSV parser, doesn't handle quoted commas or escapes
    return line.split(',')


def retry_operation(func, retries=3):
    """Retry helper — 🟡 LOW: catches everything including SystemExit."""
    for i in range(retries):
        try:
            return func()
        except:
            if i == retries - 1:
                raise


# 🟡 LOW: unreachable code after NoReturn
def abort(message: str):
    raise RuntimeError(message)
    print("This will never print")  # dead code


def merge_dicts(a, b):
    """Merge two dicts — 🟡 LOW: mutates input and ignores duplicate keys."""
    a.update(b)
    return a


# 🟡 LOW: unused import of 'json' at module level (json imported but only used here)
def to_json(data):
    return json.dumps(data)
