#!/usr/bin/env python3
"""
Replace the broken downloadMedia fallback with a Node.js-based CDN download + HKDF decryption.
The issue: WhatsApp Web's internal downloadAndMaybeDecrypt is broken (addAnnotations error).
The fix: Get media metadata from the browser, download encrypted file from CDN, decrypt in Node.js.
"""

filepath = "/home/firaz/backend/bisnesgpt-server/bots/handleMessagesTemplateWweb.js"

with open(filepath, "r") as f:
    content = f.read()

old_block = '''  try {
    console.log("[PDF] Starting PDF document processing with Poppler...");

    // Try downloadMedia with fallback for WWebJS addAnnotations error
    let media = null;
    try {
      media = await msg.downloadMedia();
    } catch (downloadErr) {
      console.log("[PDF] downloadMedia() failed:", downloadErr.message);
      console.log("[PDF] Attempting fallback media download via direct decryption...");

      try {
        const result = await client.pupPage.evaluate(async (msgId) => {
          const msg = window.Store.Msg.get(msgId) || (await window.Store.Msg.getMessagesById([msgId]))?.messages?.[0];
          if (!msg) return null;

          try {
            const decryptedMedia = await window.Store.DownloadManager.downloadAndMaybeDecrypt({
              directPath: msg.directPath,
              encFilehash: msg.encFilehash,
              filehash: msg.filehash,
              mediaKey: msg.mediaKey,
              mediaKeyTimestamp: msg.mediaKeyTimestamp,
              type: msg.type,
              signal: (new AbortController).signal
            });

            const data = await window.WWebJS.arrayBufferToBase64Async(decryptedMedia);
            return {
              data,
              mimetype: msg.mimetype,
              filename: msg.filename,
              filesize: msg.size
            };
          } catch (e) {
            return null;
          }
        }, msg.id._serialized);

        if (result) {
          media = result;
          console.log("[PDF] Fallback download succeeded!");
        }
      } catch (fallbackErr) {
        console.error("[PDF] Fallback download also failed:", fallbackErr.message);
      }
    }

    if (!media || !media.data) {
      console.error("[PDF] All download methods failed");
      return "[Error: Unable to download PDF. Please try resending the file.]";
    }

    // Convert base64 to buffer
    const buffer = Buffer.from(media.data, "base64");'''

new_block = '''  try {
    console.log("[PDF] Starting PDF document processing with Poppler...");

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
            filehash: m.filehash,
            encFilehash: m.encFilehash,
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
          const mediaTypeMap = {
            'document': 'WhatsApp Document Keys',
            'image': 'WhatsApp Image Keys',
            'video': 'WhatsApp Video Keys',
            'audio': 'WhatsApp Audio Keys',
            'ptt': 'WhatsApp Audio Keys',
            'sticker': 'WhatsApp Image Keys',
          };
          const hkdfInfo = mediaTypeMap[mediaInfo.type] || 'WhatsApp Document Keys';

          // HKDF expand (SHA-256)
          function hkdfExpand(key, info, length) {
            const infoBuffer = Buffer.from(info, 'utf8');
            let prev = Buffer.alloc(0);
            let result = Buffer.alloc(0);
            let counter = 1;
            while (result.length < length) {
              const hmac = cryptoNode.createHmac('sha256', key);
              hmac.update(Buffer.concat([prev, infoBuffer, Buffer.from([counter])]));
              prev = hmac.digest();
              result = Buffer.concat([result, prev]);
              counter++;
            }
            return result.slice(0, length);
          }

          // HKDF extract then expand
          const salt = Buffer.alloc(32, 0);
          const prk = cryptoNode.createHmac('sha256', salt).update(mediaKeyBuf).digest();
          const derivedKey = hkdfExpand(prk, hkdfInfo, 112);

          const iv = derivedKey.slice(0, 16);
          const cipherKey = derivedKey.slice(16, 48);
          const macKey = derivedKey.slice(48, 80);

          // The encrypted file format: [enc_data (n-10 bytes)][mac (10 bytes)]
          const fileData = encData.slice(0, encData.length - 10);
          // const mac = encData.slice(encData.length - 10);

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
    const buffer = Buffer.from(media.data, "base64");'''

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    with open(filepath, "w") as f:
        f.write(content)
    print("PATCH V2 APPLIED SUCCESSFULLY - PDF handler now uses CDN download + Node.js decryption")
else:
    print("ERROR: Could not find the old block to replace")
    # Debug: find approximate location
    idx = content.find("[PDF] Starting PDF document processing with Poppler")
    if idx > -1:
        print(f"Found marker at position {idx}")
        print("Context:", repr(content[idx-50:idx+200]))
    else:
        print("Marker not found at all")
