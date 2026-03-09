#!/usr/bin/env python3
"""Fix processMessageMedia fallback to use msg._data instead of browser Store"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    lines = f.readlines()

# Find the fallback section in processMessageMedia
start_marker = '      console.log(`[Media] downloadMedia() failed for'
end_marker = '    if (!media) {'

# We need to find these INSIDE processMessageMedia (not handlePDFMessage)
func_start = None
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if 'async function processMessageMedia(msg)' in line:
        func_start = i
    if func_start and start_marker in line and start_idx is None:
        start_idx = i
    if func_start and start_idx and end_marker in line and i > start_idx:
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"ERROR: Could not find markers. func={func_start}, start={start_idx}, end={end_idx}")
    exit(1)

print(f"Replacing processMessageMedia fallback: lines {start_idx+1} to {end_idx}")

replacement = '''      console.log(`[Media] downloadMedia() failed for ${msg.id._serialized}: ${downloadErr.message}`);
      // Fallback: use msg._data directly to download from CDN and decrypt
      try {
        const directPath = msg._data.directPath || msg.directPath;
        const mediaKeyB64 = msg._data.mediaKey || msg.mediaKey;
        const mimetype = msg._data.mimetype;
        const filename = msg._data.filename;

        if (directPath && mediaKeyB64) {
          const cdnUrl = `https://mmg.whatsapp.net${directPath}`;
          const cdnResponse = await axios.get(cdnUrl, {
            responseType: 'arraybuffer',
            headers: { 'Origin': 'https://web.whatsapp.com', 'Referer': 'https://web.whatsapp.com/' },
            timeout: 30000,
          });
          const encData = Buffer.from(cdnResponse.data);
          const cryptoNode = require('crypto');
          const mediaKeyBuf = Buffer.from(mediaKeyB64, 'base64');
          const mediaTypeMap = {
            'document': 'WhatsApp Document Keys', 'image': 'WhatsApp Image Keys',
            'video': 'WhatsApp Video Keys', 'audio': 'WhatsApp Audio Keys',
            'ptt': 'WhatsApp Audio Keys', 'sticker': 'WhatsApp Image Keys',
          };
          const hkdfInfo = mediaTypeMap[msg.type] || 'WhatsApp Document Keys';
          const salt = Buffer.alloc(32, 0);
          const prk = cryptoNode.createHmac('sha256', salt).update(mediaKeyBuf).digest();
          let prev = Buffer.alloc(0), okm = Buffer.alloc(0);
          const infoBuf = Buffer.from(hkdfInfo, 'utf8');
          for (let c = 1; okm.length < 112; c++) {
            const h = cryptoNode.createHmac('sha256', prk);
            h.update(Buffer.concat([prev, infoBuf, Buffer.from([c])]));
            prev = h.digest();
            okm = Buffer.concat([okm, prev]);
          }
          const iv = okm.slice(0, 16);
          const cipherKey = okm.slice(16, 48);
          const fileData = encData.slice(0, encData.length - 10);
          const decipher = cryptoNode.createDecipheriv('aes-256-cbc', cipherKey, iv);
          const decrypted = Buffer.concat([decipher.update(fileData), decipher.final()]);
          media = { data: decrypted.toString('base64'), mimetype, filename, filesize: decrypted.length };
          console.log(`[Media] CDN fallback succeeded for ${msg.id._serialized}`);
        }
      } catch (fallbackErr) {
        console.error(`[Media] CDN fallback failed for ${msg.id._serialized}:`, fallbackErr.message);
      }
    }
'''

new_lines = lines[:start_idx] + [replacement] + lines[end_idx:]

with open(filepath, "w") as f:
    f.writelines(new_lines)

print("processMessageMedia fallback updated to use msg._data")
