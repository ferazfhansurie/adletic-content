#!/usr/bin/env python3
"""
Fix: Use msg._data directly instead of querying browser Store.
The media metadata (directPath, mediaKey, etc.) is already on the msg object.
"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    lines = f.readlines()

# Find the fallback section in handlePDFMessage
start_marker = '      console.log("[PDF] Attempting fallback: CDN download + Node.js decryption...");'
end_marker = '    if (!media || !media.data) {'

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if start_marker in line and start_idx is None:
        start_idx = i
    if start_idx is not None and end_marker in line and i > start_idx:
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"ERROR: Could not find markers. start={start_idx}, end={end_idx}")
    # Debug
    for i, line in enumerate(lines):
        if 'Attempting fallback' in line:
            print(f"Found 'Attempting fallback' at line {i+1}: {line.rstrip()}")
        if 'All download methods failed' in line:
            print(f"Found 'All download methods' at line {i+1}: {line.rstrip()}")
    exit(1)

print(f"Replacing lines {start_idx+1} to {end_idx}")

replacement = '''      console.log("[PDF] Attempting fallback: CDN download using msg._data...");

      try {
        // Use media metadata directly from the message object (no browser query needed)
        const directPath = msg._data.directPath || msg.directPath;
        const mediaKeyB64 = msg._data.mediaKey || msg.mediaKey;
        const mimetype = msg._data.mimetype || 'application/pdf';
        const filename = msg._data.filename;

        if (directPath && mediaKeyB64) {
          console.log("[PDF] Got media metadata from msg._data, downloading from CDN...");

          // Download encrypted file from WhatsApp CDN
          const cdnUrl = `https://mmg.whatsapp.net${directPath}`;
          const cdnResponse = await axios.get(cdnUrl, {
            responseType: 'arraybuffer',
            headers: {
              'Origin': 'https://web.whatsapp.com',
              'Referer': 'https://web.whatsapp.com/',
            },
            timeout: 30000,
          });

          const encData = Buffer.from(cdnResponse.data);
          console.log("[PDF] Downloaded encrypted file from CDN, size:", encData.length);

          // Decrypt using HKDF + AES-256-CBC (WhatsApp E2E media encryption)
          const cryptoNode = require('crypto');
          const mediaKeyBuf = Buffer.from(mediaKeyB64, 'base64');
          const hkdfInfo = 'WhatsApp Document Keys';

          // HKDF extract + expand (SHA-256)
          const salt = Buffer.alloc(32, 0);
          const prk = cryptoNode.createHmac('sha256', salt).update(mediaKeyBuf).digest();
          let prev = Buffer.alloc(0);
          let okm = Buffer.alloc(0);
          const infoBuffer = Buffer.from(hkdfInfo, 'utf8');
          for (let counter = 1; okm.length < 112; counter++) {
            const hmac = cryptoNode.createHmac('sha256', prk);
            hmac.update(Buffer.concat([prev, infoBuffer, Buffer.from([counter])]));
            prev = hmac.digest();
            okm = Buffer.concat([okm, prev]);
          }
          const derivedKey = okm.slice(0, 112);
          const iv = derivedKey.slice(0, 16);
          const cipherKey = derivedKey.slice(16, 48);

          // Encrypted file format: [enc_data][10-byte mac]
          const fileData = encData.slice(0, encData.length - 10);

          // Decrypt with AES-256-CBC
          const decipher = cryptoNode.createDecipheriv('aes-256-cbc', cipherKey, iv);
          const decrypted = Buffer.concat([decipher.update(fileData), decipher.final()]);

          console.log("[PDF] Decrypted media successfully, size:", decrypted.length);
          media = {
            data: decrypted.toString('base64'),
            mimetype: mimetype,
            filename: filename,
            filesize: decrypted.length,
          };
          console.log("[PDF] Fallback CDN download + decryption succeeded!");
        } else {
          console.error("[PDF] No directPath or mediaKey on msg._data");
          console.error("[PDF] directPath:", directPath, "mediaKey:", mediaKeyB64 ? "present" : "missing");
        }
      } catch (fallbackErr) {
        console.error("[PDF] CDN fallback failed:", fallbackErr.message);
        if (fallbackErr.stack) console.error("[PDF] Stack:", fallbackErr.stack);
      }
    }

'''

new_lines = lines[:start_idx] + [replacement] + lines[end_idx:]

with open(filepath, "w") as f:
    f.writelines(new_lines)

print("PATCH V4 APPLIED - using msg._data directly instead of browser Store")
