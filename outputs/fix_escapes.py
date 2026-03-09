#!/usr/bin/env python3
"""Fix escaped exclamation marks introduced by the patch"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    content = f.read()

# Count occurrences of \!
count = content.count("\\!")
print(f"Found {count} instances of \\!")

# Only fix them - replace \! with !
# But be careful - only fix the ones we introduced (in our patched sections)
# Actually, let's check if \! appears elsewhere in the original code
# The safe approach: replace all \! since JS doesn't use \! as valid syntax
content = content.replace("\\!", "!")

with open(filepath, "w") as f:
    f.write(content)

print(f"Fixed {count} escaped exclamation marks")
