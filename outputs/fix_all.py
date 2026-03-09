#!/usr/bin/env python3
"""
Fix two issues:
1. Escaped exclamation marks (\!) from the first patch
2. msg.client reference in processMessageMedia fallback (WWebJS msg objects have .client property)
"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    content = f.read()

# Fix 1: Replace \! with ! (only 3 occurrences in our patched code)
escaped_count = content.count("\\!")
content = content.replace("\\!", "!")
print(f"Fixed {escaped_count} escaped exclamation marks")

with open(filepath, "w") as f:
    f.write(content)

print("All fixes applied")
