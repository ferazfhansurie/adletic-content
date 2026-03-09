#!/usr/bin/env python3
"""Replace entire handlePDFMessage download section using line-based approach"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    lines = f.readlines()

# Find the start and end of the section to replace
start_marker = '    console.log("[PDF] Starting PDF document processing with Poppler...");'
end_marker = '    const buffer = Buffer.from(media.data, "base64");'

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if start_marker in line and start_idx is None:
        start_idx = i
    if end_marker in line and start_idx is not None:
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"ERROR: Could not find markers. start={start_idx}, end={end_idx}")
    exit(1)

print(f"Found section: lines {start_idx+1} to {end_idx+1}")

replacement = '''    console.log("[PDF] Starting PDF document processing with Poppler...");

    // Try downloadMedia with fallback for WWebJS addAnnotations error
    let media = null;
    try {
      media = await msg.downloadMedia();
    } catch (downloadErr) {
      console.log("[PDF] downloadMedia() failed:", downloadErr.message);
      console.log("[PDF] Attempting fallback: CDN download + Node.js decryption...");

      try {
        // Step 1: Get media metadata from the browser (without calling downloadAndMaybeDecrypt)
        const mediaInfo = await client.pupPage.evaluate(async (msgId) => {
          const m = window.Store.Msg.get(msgId) || (await window.Store.Msg.getMessagesById([msgId]))?.messages?.[0];
          if (!m) return null;
          return {
            directPath: m.directPath,
            mediaKey: m.mediaKey ? btoa(String.fromCharCode(...new Uint8Array(m.mediaKey))) : null,
            type: m.type,
            mimetype: m.mimetype,
            filename: m.filename,
            size: m.size,
          };
        }, msg.id._serialized);

        if (mediaInfo && mediaInfo.directPath && mediaInfo.mediaKey) {
          console.log("[PDF] Got media metadata, downloading from CDN...");

          // Step 2: Download encrypted file from WhatsApp CDN
          const cdnUrl = `https://mmg.whatsapp.net${mediaInfo.directPath}`;
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

          // Step 3: Decrypt using HKDF + AES-256-CBC (WhatsApp E2E media encryption)
          const cryptoNode = require('crypto');
          const mediaKeyBuf = Buffer.from(mediaInfo.mediaKey, 'base64');

          // WhatsApp media type info strings for HKDF
          const hkdfInfo = 'WhatsApp Document Keys';

          // HKDF extract + expand (SHA-256)
          const salt = Buffer.alloc(32, 0);
          const prk = cryptoNode.createHmac('sha256', salt).update(mediaKeyBuf).digest();

          // HKDF expand
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

          console.log("[PDF] Decrypted media, size:", decrypted.length);
          media = {
            data: decrypted.toString('base64'),
            mimetype: mediaInfo.mimetype || 'application/pdf',
            filename: mediaInfo.filename,
            filesize: decrypted.length,
          };
          console.log("[PDF] Fallback CDN download + decryption succeeded!");
        } else {
          console.error("[PDF] Could not get media metadata from browser");
        }
      } catch (fallbackErr) {
        console.error("[PDF] CDN fallback failed:", fallbackErr.message);
        if (fallbackErr.stack) console.error("[PDF] Stack:", fallbackErr.stack);
      }
    }

    if (!media || !media.data) {
      console.error("[PDF] All download methods failed");
      return "[Error: Unable to download PDF. Please try resending the file.]";
    }

    // Convert base64 to buffer
    const buffer = Buffer.from(media.data, "base64");
'''

new_lines = lines[:start_idx] + [replacement] + lines[end_idx+1:]

with open(filepath, "w") as f:
    f.writelines(new_lines)

print("PATCH V3 APPLIED SUCCESSFULLY")
