/**
 * Extracts a target social media or video URL from incoming window / router location.
 * Supports:
 * - Query params: ?url=, ?link=, ?q=, ?search=, ?query=, ?s=, ?target=, ?video=, ?media=
 * - Raw query without parameter name: ?https://www.instagram.com/...
 * - Hash parameters or raw hash: #https://... or #url=https://...
 * - Path appended URLs: /https://www.instagram.com/...
 */
export function extractIncomingUrl(locationObj) {
  if (typeof window === 'undefined') return '';

  const search = locationObj?.search || window.location.search || '';
  const hash = locationObj?.hash || window.location.hash || '';
  const pathname = locationObj?.pathname || window.location.pathname || '';

  // Helper to validate and clean extracted candidate
  function cleanCandidate(raw) {
    if (!raw || typeof raw !== 'string') return '';
    let decoded = raw.trim();
    try {
      decoded = decodeURIComponent(decoded);
    } catch (e) {
      // ignore malformed uri decode
    }
    // Also handle double-encoded URLs
    if (decoded.includes('%3A%2F%2F') || decoded.includes('%3a%2f%2f')) {
      try {
        decoded = decodeURIComponent(decoded);
      } catch (e) {}
    }
    // Ensure candidate starts with http://, https://, or social domain pattern
    if (/^(https?:\/\/|[a-z0-9-]+\.(com|org|net|in|co|ly|be|app|tv|page|short|is|ai|io)\/)/i.test(decoded)) {
      if (!decoded.startsWith('http://') && !decoded.startsWith('https://')) {
        decoded = `https://${decoded}`;
      }
      return decoded;
    }
    return '';
  }

  // 1. Check Search Parameters
  if (search) {
    const rawSearch = search.replace(/^\?/, '').trim();

    // Check if the search string itself is a raw URL
    const rawCheck = cleanCandidate(rawSearch);
    if (rawCheck) return rawCheck;

    try {
      const params = new URLSearchParams(search);
      const keysToCheck = ['url', 'link', 'q', 'search', 'query', 's', 'target', 'video', 'media', 'text', 'post'];
      for (const k of keysToCheck) {
        const val = params.get(k);
        const cleaned = cleanCandidate(val);
        if (cleaned) return cleaned;
      }

      // Check for bare key parameters (e.g. ?https://instagram.com/reel/...)
      for (const key of params.keys()) {
        const cleaned = cleanCandidate(key);
        if (cleaned) return cleaned;
      }
    } catch (e) {
      // fallback
    }
  }

  // 2. Check Hash Fragment
  if (hash) {
    const rawHash = hash.replace(/^#/, '').trim();
    const rawCheck = cleanCandidate(rawHash);
    if (rawCheck) return rawCheck;

    if (rawHash.includes('=')) {
      try {
        const hashParams = new URLSearchParams(rawHash);
        const keysToCheck = ['url', 'link', 'q', 'search', 'target'];
        for (const k of keysToCheck) {
          const val = hashParams.get(k);
          const cleaned = cleanCandidate(val);
          if (cleaned) return cleaned;
        }
      } catch (e) {}
    }
  }

  // 3. Check Pathname for appended URLs (e.g. /https://www.youtube.com/watch?v=...)
  if (pathname) {
    const pathMatch = pathname.match(/^\/(https?:\/\/.+)/i);
    if (pathMatch) {
      const cleaned = cleanCandidate(pathMatch[1]);
      if (cleaned) return cleaned;
    }
  }

  return '';
}
