/**
 * OVD Traffic Origin & Referrer Attribution Engine
 * Tracks document.referrer, search engine origins, social referrals, UTM parameters,
 * and persists first-touch & session attribution in local/sessionStorage.
 */

const KNOWN_SEARCH_ENGINES = [
  { pattern: /(?:^|\.)google\./i, name: 'Google' },
  { pattern: /(?:^|\.)bing\./i, name: 'Bing' },
  { pattern: /(?:^|\.)yahoo\./i, name: 'Yahoo' },
  { pattern: /(?:^|\.)duckduckgo\./i, name: 'DuckDuckGo' },
  { pattern: /(?:^|\.)yandex\./i, name: 'Yandex' },
  { pattern: /(?:^|\.)ecosia\./i, name: 'Ecosia' },
  { pattern: /(?:^|\.)baidu\./i, name: 'Baidu' },
  { pattern: /(?:^|\.)ask\.com/i, name: 'Ask' },
  { pattern: /(?:^|\.)search\.brave\./i, name: 'Brave' },
];

const KNOWN_SOCIAL_PLATFORMS = [
  { pattern: /(?:^|\.)(?:twitter\.com|x\.com|t\.co)/i, name: 'X (Twitter)' },
  { pattern: /(?:^|\.)(?:facebook\.com|fb\.com|fb\.me|m\.facebook\.com)/i, name: 'Facebook' },
  { pattern: /(?:^|\.)(?:instagram\.com|instagr\.am)/i, name: 'Instagram' },
  { pattern: /(?:^|\.)(?:youtube\.com|youtu\.be)/i, name: 'YouTube' },
  { pattern: /(?:^|\.)(?:tiktok\.com|vm\.tiktok\.com)/i, name: 'TikTok' },
  { pattern: /(?:^|\.)(?:reddit\.com|redd\.it)/i, name: 'Reddit' },
  { pattern: /(?:^|\.)(?:pinterest\.com|pin\.it)/i, name: 'Pinterest' },
  { pattern: /(?:^|\.)(?:threads\.net)/i, name: 'Threads' },
  { pattern: /(?:^|\.)(?:linkedin\.com|lnkd\.in)/i, name: 'LinkedIn' },
  { pattern: /(?:^|\.)(?:t\.me|telegram\.org)/i, name: 'Telegram' },
  { pattern: /(?:^|\.)(?:wa\.me|whatsapp\.com)/i, name: 'WhatsApp' },
  { pattern: /(?:^|\.)(?:quora\.com)/i, name: 'Quora' },
  { pattern: /(?:^|\.)(?:tumblr\.com)/i, name: 'Tumblr' },
];

export function parseTrafficOrigin(referrerUrl = '') {
  const currentHost = typeof window !== 'undefined' ? window.location.hostname : '';
  const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();

  // 1. Check UTM and Campaign URL Parameters First
  const utmSource = searchParams.get('utm_source');
  const utmMedium = searchParams.get('utm_medium');
  const utmCampaign = searchParams.get('utm_campaign');
  const utmContent = searchParams.get('utm_content');
  const utmTerm = searchParams.get('utm_term');
  const refParam = searchParams.get('ref') || searchParams.get('source');
  const gclid = searchParams.get('gclid');
  const fbclid = searchParams.get('fbclid');
  const ttclid = searchParams.get('ttclid');

  let referrerHost = '';
  try {
    if (referrerUrl) {
      referrerHost = new URL(referrerUrl).hostname.toLowerCase();
    }
  } catch (e) {
    referrerHost = '';
  }

  // 2. Classify Origin
  let channel = 'Direct';
  let source = utmSource || refParam || 'direct';
  let medium = utmMedium || 'none';

  if (gclid) {
    channel = 'Paid Search';
    source = utmSource || 'google';
    medium = utmMedium || 'cpc';
  } else if (fbclid) {
    channel = 'Paid/Organic Social';
    source = utmSource || 'facebook';
    medium = utmMedium || 'social';
  } else if (ttclid) {
    channel = 'Paid/Organic Social';
    source = utmSource || 'tiktok';
    medium = utmMedium || 'social';
  } else if (utmSource || utmMedium) {
    channel = 'Campaign';
  } else if (referrerHost) {
    // Check if internal referrer
    if (currentHost && referrerHost === currentHost) {
      channel = 'Internal Navigation';
      source = 'internal';
      medium = 'internal';
    } else {
      // Check Search Engines
      const searchEngine = KNOWN_SEARCH_ENGINES.find(se => se.pattern.test(referrerHost));
      if (searchEngine) {
        channel = 'Organic Search';
        source = searchEngine.name.toLowerCase();
        medium = 'organic';
      } else {
        // Check Social Networks
        const socialNet = KNOWN_SOCIAL_PLATFORMS.find(sn => sn.pattern.test(referrerHost));
        if (socialNet) {
          channel = 'Social Referral';
          source = socialNet.name.toLowerCase();
          medium = 'social';
        } else {
          // Other Websites
          channel = 'Web Referral';
          source = referrerHost;
          medium = 'referral';
        }
      }
    }
  }

  return {
    channel,
    source,
    medium,
    campaign: utmCampaign || null,
    term: utmTerm || null,
    content: utmContent || null,
    referrerUrl: referrerUrl || null,
    referrerHost: referrerHost || null,
    landingPage: typeof window !== 'undefined' ? window.location.pathname + window.location.search : '/',
    timestamp: new Date().toISOString()
  };
}

const STORAGE_KEY_FIRST = 'ovd_attribution_first_touch';
const STORAGE_KEY_SESSION = 'ovd_attribution_session';

/**
 * Initializes traffic attribution. Call on application mount.
 */
export function initAttribution() {
  if (typeof window === 'undefined') return null;

  const currentAttribution = parseTrafficOrigin(document.referrer);

  // 1. Session Touch: Updates per browsing session if not already set or if non-internal
  try {
    const existingSession = sessionStorage.getItem(STORAGE_KEY_SESSION);
    if (!existingSession || currentAttribution.channel !== 'Internal Navigation') {
      sessionStorage.setItem(STORAGE_KEY_SESSION, JSON.stringify(currentAttribution));
    }
  } catch (e) {
    // Storage quota or privacy mode
  }

  // 2. First Touch: Persists permanently to record where user originally came from
  try {
    const existingFirst = localStorage.getItem(STORAGE_KEY_FIRST);
    if (!existingFirst && currentAttribution.channel !== 'Internal Navigation') {
      localStorage.setItem(STORAGE_KEY_FIRST, JSON.stringify(currentAttribution));
    }
  } catch (e) {
    // Storage quota or privacy mode
  }

  return currentAttribution;
}

/**
 * Returns full attribution payload for API requests or debugging
 */
export function getAttribution() {
  if (typeof window === 'undefined') {
    return { firstTouch: null, sessionTouch: null, current: null };
  }

  let firstTouch = null;
  let sessionTouch = null;

  try {
    const rawFirst = localStorage.getItem(STORAGE_KEY_FIRST);
    if (rawFirst) firstTouch = JSON.parse(rawFirst);
  } catch (e) {}

  try {
    const rawSession = sessionStorage.getItem(STORAGE_KEY_SESSION);
    if (rawSession) sessionTouch = JSON.parse(rawSession);
  } catch (e) {}

  const current = parseTrafficOrigin(document.referrer);

  return {
    firstTouch: firstTouch || current,
    sessionTouch: sessionTouch || current,
    current,
    device: {
      screenWidth: window.innerWidth,
      screenHeight: window.innerHeight,
      language: navigator.language || 'en',
      platform: navigator.platform || 'unknown'
    }
  };
}

/**
 * Generates custom HTTP headers to pass along with fetch requests
 */
export function getAttributionHeaders() {
  const attr = getAttribution();
  const active = attr.firstTouch || attr.current;
  return {
    'X-OVD-Source': active?.source || 'direct',
    'X-OVD-Medium': active?.medium || 'none',
    'X-OVD-Channel': active?.channel || 'Direct',
    'X-OVD-Referrer': active?.referrerHost || 'none'
  };
}
