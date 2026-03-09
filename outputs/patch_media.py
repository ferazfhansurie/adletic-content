#!/usr/bin/env python3
"""Patch processMessageMedia in handleMessagesTemplateWweb.js to add downloadMedia fallback"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    content = f.read()

# Find processMessageMedia function
func_start = content.find("async function processMessageMedia")
if func_start == -1:
    print("ERROR: processMessageMedia not found")
    exit(1)

# Find the try block with downloadMedia inside this function
search_area = content[func_start:]
old_pattern = '  try {\n    const media = await msg.downloadMedia();'
pos = search_area.find(old_pattern)
if pos == -1:
    print("ERROR: downloadMedia pattern not found in processMessageMedia")
    exit(1)

abs_pos = func_start + pos

# The old block to replace
old_block = """  try {
    const media = await msg.downloadMedia();
    if (!media) {
      console.log(
        `Failed to download media for message: ${msg.id._serialized}`
      );
      return null;
    }"""

# Verify it matches
actual = content[abs_pos:abs_pos+len(old_block)]
if actual != old_block:
    print("ERROR: Block mismatch")
    print("Expected:", repr(old_block[:100]))
    print("Got:", repr(actual[:100]))
    exit(1)

new_block = """  try {
    let media = null;
    try {
      media = await msg.downloadMedia();
    } catch (downloadErr) {
      console.log(`[Media] downloadMedia() failed for ${msg.id._serialized}: ${downloadErr.message}`);
      console.log("[Media] Attempting fallback via direct decryption...");
      try {
        const result = await msg.client.pupPage.evaluate(async (msgId) => {
          const m = window.Store.Msg.get(msgId) || (await window.Store.Msg.getMessagesById([msgId]))?.messages?.[0];
          if (!m) return null;
          try {
            const decryptedMedia = await window.Store.DownloadManager.downloadAndMaybeDecrypt({
              directPath: m.directPath,
              encFilehash: m.encFilehash,
              filehash: m.filehash,
              mediaKey: m.mediaKey,
              mediaKeyTimestamp: m.mediaKeyTimestamp,
              type: m.type,
              signal: (new AbortController).signal
            });
            const data = await window.WWebJS.arrayBufferToBase64Async(decryptedMedia);
            return { data, mimetype: m.mimetype, filename: m.filename, filesize: m.size };
          } catch (e) { return null; }
        }, msg.id._serialized);
        if (result) {
          media = result;
          console.log("[Media] Fallback download succeeded!");
        }
      } catch (fallbackErr) {
        console.error("[Media] Fallback also failed:", fallbackErr.message);
      }
    }
    if (!media) {
      console.log(
        `Failed to download media for message: ${msg.id._serialized}`
      );
      return null;
    }"""

content = content[:abs_pos] + new_block + content[abs_pos+len(old_block):]

with open(filepath, "w") as f:
    f.write(content)

print("PATCH 2 APPLIED SUCCESSFULLY")
