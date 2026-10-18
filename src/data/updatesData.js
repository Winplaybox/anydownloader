export const releaseUpdates = [
  {
    version: 'v2.5',
    date: 'October 18, 2026',
    title: 'Platform-Nested Routing, Live Social Blog & Product Changelog',
    badge: 'Latest Release',
    badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    description: 'Refined header navigation, removed redundant badges, expanded clean platform namespaces (/youtube/..., /facebook/...), launched live Social Media Updates Blog and Official Releases changelog.',
    highlights: [
      {
        tag: 'Navigation & UI',
        color: 'text-rose-400',
        text: 'Cleaned up header navigation bar: removed redundant badges, merged Top YouTube Channels directly into YouTube category.'
      },
      {
        tag: 'New Feature',
        color: 'text-emerald-400',
        text: 'Launched Real-Time Social Media Blog (/blogs) covering algorithm shifts, TikTok encoding rules, and creator monetization.'
      },
      {
        tag: 'New Feature',
        color: 'text-cyan-400',
        text: 'Added Official Updates & Product Changelog (/updates) tracking all features, engine enhancements, and security releases.'
      },
      {
        tag: 'Architecture',
        color: 'text-amber-400',
        text: 'Established scalable /youtube/..., /facebook/..., /instagram/..., and /tiktok/... URL routing architecture.'
      }
    ]
  },
  {
    version: 'v2.4',
    date: 'October 18, 2026',
    title: 'Multi-Page Architecture & Google AdSense Optimization',
    badge: 'Major',
    badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    description: 'Transitioned from a single-page utility to a dedicated multi-page platform with full SEO guides, AdSense compliance pages, and responsive display units.',
    highlights: [
      {
        tag: 'Compliance',
        color: 'text-rose-400',
        text: 'Added dedicated Privacy Policy (GDPR/CCPA/DART cookies), Terms of Service, and Contact Us pages.'
      },
      {
        tag: 'SEO & Performance',
        color: 'text-emerald-400',
        text: 'Created standalone tool landing pages with in-depth technical guides and platform-specific FAQs.'
      },
      {
        tag: 'Cache Busting',
        color: 'text-cyan-400',
        text: 'Automated content-hashed asset compilation to eliminate stale browser caching.'
      }
    ]
  },
  {
    version: 'v2.3',
    date: 'October 18, 2026',
    title: 'Top 100 YouTube Channels Global Database (12H Auto-Sync)',
    badge: 'Feature',
    badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    description: 'Introduced an automated 12-hour global subscriber ranking engine indexing the worlds top 100 YouTube channels with country flags and category genres.',
    highlights: [
      {
        tag: 'Ranking Engine',
        color: 'text-amber-400',
        text: 'Automated 12-hour synchronization cycles tracking subscriber milestones, video count, and views.'
      },
      {
        tag: 'Filtering',
        color: 'text-cyan-400',
        text: 'Integrated 12 country filters (USA, India, Brazil, Japan, UK, etc.) and 12 content categories.'
      },
      {
        tag: 'Interactive Search',
        color: 'text-emerald-400',
        text: 'Instant fuzzy search for any creator handle or channel title.'
      }
    ]
  },
  {
    version: 'v2.2',
    date: 'October 18, 2026',
    title: 'YouTube Multi-Tool Suite: MP3, Transcripts & Subtitles',
    badge: 'Feature',
    badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    description: 'Expanded beyond video downloads to include high-bitrate MP3 extraction, timestamped transcript cues, multi-language subtitle tracks, and all thumbnail resolutions.',
    highlights: [
      {
        tag: 'Audio Engine',
        color: 'text-purple-400',
        text: 'High-fidelity 320kbps and 192kbps MP3 audio conversion.'
      },
      {
        tag: 'Transcripts',
        color: 'text-rose-400',
        text: 'Searchable timestamped transcript cues with one-click .TXT file download.'
      },
      {
        tag: 'Subtitles',
        color: 'text-cyan-400',
        text: 'Extracted multi-language SRT and VTT closed-caption tracks for VLC and editing software.'
      },
      {
        tag: 'Thumbnails',
        color: 'text-emerald-400',
        text: 'One-click downloads for 1080p Maxres, 720p HQ, 480p SD, and 360p MQ image covers.'
      }
    ]
  },
  {
    version: 'v2.0',
    date: 'October 18, 2026',
    title: 'Render Cloud Backend & Zero-Rate-Limit Streaming Gateway',
    badge: 'Core',
    badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    description: 'Replaced insecure direct client calls with a hardened Python streaming gateway running on Render with origin validation.',
    highlights: [
      {
        tag: 'Security',
        color: 'text-rose-400',
        text: 'Enforced origin verification rejecting unauthorized API access with 403 Forbidden.'
      },
      {
        tag: 'Reliability',
        color: 'text-emerald-400',
        text: 'Dual-pipeline extraction with mobile client emulation and official oEmbed fallback for 100% uptime.'
      }
    ]
  }
];
