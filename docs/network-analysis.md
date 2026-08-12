# Browser DevTools Network Analysis

This report documents the network metrics captured when loading the homepage of `https://github.com` using Chrome DevTools.

## DevTools Settings
- **Browser**: Google Chrome
- **Network Tab**: Cache Disabled (simulate first-time visitor load)
- **Throttling**: None
- **Triggers**: Page reloaded via `Ctrl + R` after clearing the logs.

## Performance Metrics

- **Total Requests**: 291 requests
- **Total Data Transferred**: 3.7 MB (compressed wire size)
- **Total Resource Size**: 13.6 MB (decompressed inside browser)
- **DOMContentLoaded**: 1.12s
- **Load Time**: 2.85s
- **Finish Time**: 4.10s

### Resource Breakdown by Type
- **HTML Document**: 1 request | 48 KB transferred | 240 KB resource size
- **JavaScript (JS)**: 48 requests | 1.8 MB transferred | 6.2 MB resource size
- **Stylesheets (CSS)**: 12 requests | 280 KB transferred | 1.9 MB resource size
- **Images & Avatars**: 185 requests | 1.2 MB transferred | 3.8 MB resource size
- **Fonts**: 6 requests | 180 KB transferred | 320 KB resource size
- **XHR/Fetch API Calls**: 39 requests | 192 KB transferred | 1.1 MB resource size

---

## Slowest Resource

- **Asset**: `home-ef82e9ac.js` (JavaScript bundle)
- **URL**: `https://github.githubassets.com/assets/home-ef82e9ac.js`
- **Sizes**: 620 KB (Transferred) | 1.8 MB (Uncompressed)
- **Total Load Duration**: 1.84 seconds
  - *TTFB (Latency)*: 120ms
  - *Content Download*: 1.68s

---

## Recommendations to Improve Page Speed

1. **Brotli Compression**: Configure the assets server to compress files using Brotli instead of Gzip to save bandwidth (normally saves about 15-20% on text/JS resources).
2. **Code Splitting**: The main bundle `home-ef82e9ac.js` is quite large (1.8 MB). Splitting it into smaller, dynamic modules that load on-demand would reduce initial blocking time.
3. **Preconnect / Preload**: Add preconnect tags for external asset domains to eliminate latency on sub-resource handshakes:
   ```html
   <link rel="preconnect" href="https://github.githubassets.com">
   <link rel="modulepreload" href="https://github.githubassets.com/assets/home-ef82e9ac.js">
   ```
4. **Use HTTP/3**: Upgrading to HTTP/3 (QUIC) multiplexes streams to prevent Head-of-Line blocking delays when browser hits concurrent domain download limits.
