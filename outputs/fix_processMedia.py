#!/usr/bin/env python3
"""Fix processMessageMedia fallback to check for pupPage before using it"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    content = f.read()

old = '''      console.log("[Media] Attempting fallback via direct decryption...");
      try {
        const result = await msg.client.pupPage.evaluate(async (msgId) => {'''

new = '''      console.log("[Media] Attempting fallback via direct decryption...");
      try {
        if (!msg.client || !msg.client.pupPage) {
          throw new Error("No pupPage available (likely Meta Direct message)");
        }
        const result = await msg.client.pupPage.evaluate(async (msgId) => {'''

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, "w") as f:
        f.write(content)
    print("FIX APPLIED: Added pupPage guard in processMessageMedia")
else:
    print("ERROR: Pattern not found")
