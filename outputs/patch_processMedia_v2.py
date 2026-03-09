#!/usr/bin/env python3
"""Replace processMessageMedia fallback with CDN download approach"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    lines = f.readlines()

# Find processMessageMedia function and its downloadMedia section
func_start = None
download_start = None
download_end = None

for i, line in enumerate(lines):
    if 'async function processMessageMedia(msg)' in line:
        func_start = i
    if func_start and download_start is None and 'let media = null;' in line and i > func_start:
        download_start = i
    if func_start and download_start and 'Failed to download media for message' in line and i > download_start:
        # Find the closing of this if block (return null; })
        for j in range(i, min(i+5, len(lines))):
            if 'return null;' in lines[j]:
                download_end = j + 1  # include the closing brace line
                break
        break

if download_start is None or download_end is None:
    print(f"ERROR: Could not find section. func={func_start}, start={download_start}, end={download_end}")
    exit(1)

print(f"Found processMessageMedia download section: lines {download_start+1} to {download_end+1}")

# Check what's at download_end to include the closing brace
closing_line = lines[download_end].strip() if download_end < len(lines) else ''
print(f"Line after end: '{closing_line}'")

replacement = '''    let media = null;
    try {
      media = await msg.downloadMedia();
    } catch (downloadErr) {
      console.log(`[Media] downloadMedia() failed for ${msg.id._serialized}: ${downloadErr.message}`);
      // Fallback: try CDN download + Node.js decryption
      try {
        if (msg.client && msg.client.pupPage) {
          const mediaInfo = await msg.client.pupPage.evaluate(async (msgId) => {
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
            const cdnUrl = `https://mmg.whatsapp.net${mediaInfo.directPath}`;
            const cdnResponse = await axios.get(cdnUrl, {
              responseType: 'arraybuffer',
              headers: { 'Origin': 'https://web.whatsapp.com', 'Referer': 'https://web.whatsapp.com/' },
              timeout: 30000,
            });
            const encData = Buffer.from(cdnResponse.data);
            const cryptoNode = require('crypto');
            const mediaKeyBuf = Buffer.from(mediaInfo.mediaKey, 'base64');
            const mediaTypeMap = {
              'document': 'WhatsApp Document Keys', 'image': 'WhatsApp Image Keys',
              'video': 'WhatsApp Video Keys', 'audio': 'WhatsApp Audio Keys',
              'ptt': 'WhatsApp Audio Keys', 'sticker': 'WhatsApp Image Keys',
            };
            const hkdfInfo = mediaTypeMap[mediaInfo.type] || 'WhatsApp Document Keys';
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
            media = { data: decrypted.toString('base64'), mimetype: mediaInfo.mimetype, filename: mediaInfo.filename, filesize: decrypted.length };
            console.log(`[Media] CDN fallback succeeded for ${msg.id._serialized}`);
          }
        }
      } catch (fallbackErr) {
        console.error(`[Media] CDN fallback failed for ${msg.id._serialized}:`, fallbackErr.message);
      }
    }
    if (!media) {
      console.log(
        `Failed to download media for message: ${msg.id._serialized}`
      );
      return null;
    }
'''

new_lines = lines[:download_start] + [replacement] + lines[download_end+1:]

with open(filepath, "w") as f:
    f.writelines(new_lines)

print("PATCH processMessageMedia V2 APPLIED SUCCESSFULLY")
