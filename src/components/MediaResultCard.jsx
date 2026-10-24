import React, { useState } from 'react';
import { 
  Download, 
  Check, 
  Copy, 
  ExternalLink, 
  CheckCircle2, 
  Image as ImageIcon, 
  Video, 
  Layers, 
  Maximize2, 
  X,
  Play
} from 'lucide-react';
import { 
  TwitterXIcon,
  YoutubeIcon, 
  FacebookIcon,
  InstagramIcon, 
  TiktokIcon,
  PinterestIcon,
  RedditIcon,
  ThreadsIcon,
  GlobeIcon
} from './BrandIcons.jsx';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://anydownloader-backend-vvbj.onrender.com';

export default function MediaResultCard({ data, onReset }) {
  if (!data) return null;

  const { platform, title, author, items = [], sourceUrl } = data;
  const isMultiItem = items.length > 1;

  // Selected quality per single video item
  const [selectedVariantIdx, setSelectedVariantIdx] = useState(0);
  // Selected items for multi-item / carousel download
  const [selectedItems, setSelectedItems] = useState(() => items.map((_, i) => i));
  const [previewMedia, setPreviewMedia] = useState(null);
  const [toastMessage, setToastMessage] = useState('');
  const [isDownloadingAll, setIsDownloadingAll] = useState(false);

  function showToast(msg) {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3000);
  }

  function handleCopySource() {
    if (sourceUrl) {
      navigator.clipboard.writeText(sourceUrl);
      showToast('Source link copied to clipboard!');
    }
  }

  function triggerDownload(downloadUrl) {
    if (!downloadUrl) return;
    const finalUrl = downloadUrl.startsWith('http') ? downloadUrl : `${BACKEND_BASE}${downloadUrl}`;
    const a = document.createElement('a');
    a.href = finalUrl;
    a.setAttribute('download', '');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast('Download started!');
  }

  async function handleDownloadAll() {
    setIsDownloadingAll(true);
    showToast(`Downloading ${selectedItems.length} media items...`);
    for (let i = 0; i < selectedItems.length; i++) {
      const itemIndex = selectedItems[i];
      const item = items[itemIndex];
      if (item && item.variants && item.variants[0]) {
        triggerDownload(item.variants[0].downloadUrl);
        // Small delay between downloads so browser doesn't block multi-tabs
        await new Promise(r => setTimeout(r, 600));
      }
    }
    setIsDownloadingAll(false);
  }

  function toggleSelectItem(idx) {
    setSelectedItems(prev => 
      prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]
    );
  }

  const PlatformIcon = {
    twitter: TwitterXIcon,
    youtube: YoutubeIcon,
    facebook: FacebookIcon,
    instagram: InstagramIcon,
    tiktok: TiktokIcon,
    pinterest: PinterestIcon,
    reddit: RedditIcon,
    threads: ThreadsIcon,
    generic: GlobeIcon,
  }[platform] || Video;

  return (
    <section className="w-full max-w-4xl mx-auto px-4 pb-16 animate-in fade-in slide-in-from-bottom-3 duration-200">
      
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] shadow-[var(--shadow-2)] text-sm font-semibold animate-in slide-in-from-bottom-2 fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Container Card */}
      <div className="bg-[var(--surface)] border-2 border-[var(--border)] rounded-2xl shadow-[var(--shadow-1)] overflow-hidden">
        
        {/* Card Header: Platform Badge & Author Row */}
        <div className="p-4 sm:p-6 border-b border-[var(--border)] flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {author?.avatar ? (
              <img 
                src={author.avatar} 
                alt={author.name || 'Author'} 
                className="w-11 h-11 rounded-full object-cover border border-[var(--border)]"
                onError={(e) => { e.currentTarget.style.display = 'none'; }}
              />
            ) : (
              <div className="w-11 h-11 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] flex items-center justify-center font-bold text-sm text-[var(--text)]">
                {(author?.name || platform || 'U')[0].toUpperCase()}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base text-[var(--text)]">
                  {author?.name || (platform ? platform.toUpperCase() : 'Creator')}
                </span>
                {author?.handle && (
                  <span className="text-xs text-[var(--text-muted)] font-medium">
                    @{author.handle.replace(/^@/, '')}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-[var(--bg-alt)] text-[var(--text-muted)] border border-[var(--border)]">
                  <PlatformIcon className="w-3 h-3" />
                  <span className="capitalize">{platform}</span>
                </span>
                {isMultiItem && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-[var(--accent-bg)] text-[var(--accent)] border border-[var(--accent)]/30">
                    <Layers className="w-3 h-3" />
                    <span>{items.length} Items</span>
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopySource}
              className="p-2 rounded-lg border border-[var(--border)] hover:border-[var(--text)] text-[var(--text)] transition-colors"
              title="Copy original post URL"
            >
              <Copy className="w-4 h-4" />
            </button>
            {sourceUrl && (
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg border border-[var(--border)] hover:border-[var(--text)] text-[var(--text)] transition-colors"
                title="Open on platform"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>

        {/* Post Title / Caption */}
        {title && (
          <div className="px-4 sm:px-6 pt-4 pb-2">
            <p className="text-sm sm:text-base font-semibold text-[var(--text)] line-clamp-2">
              {title}
            </p>
          </div>
        )}

        {/* Content Body: Single Item View vs Carousel / Multi-Item Grid */}
        <div className="p-4 sm:p-6">
          {!isMultiItem ? (
            /* Single Media Item View */
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
              
              {/* Thumbnail / Preview Area */}
              <div className="md:col-span-5 relative rounded-xl overflow-hidden bg-[var(--bg-alt)] border border-[var(--border)] aspect-video md:aspect-[4/3] flex items-center justify-center group">
                {items[0]?.thumbnail ? (
                  <img
                    src={items[0].thumbnail}
                    alt={title || 'Media thumbnail'}
                    className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center p-6 text-[var(--text-muted)]">
                    <Video className="w-12 h-12 mb-2 stroke-1" />
                    <span className="text-xs font-semibold">Media Preview</span>
                  </div>
                )}

                {/* Badge for Video duration or GIF */}
                <div className="absolute top-2 left-2 flex gap-1">
                  {items[0]?.variants[0]?.quality === 'GIF' ? (
                    <span className="px-2 py-0.5 rounded-md bg-black/80 text-white text-[11px] font-bold">
                      GIF
                    </span>
                  ) : items[0]?.kind === 'video' ? (
                    <span className="px-2 py-0.5 rounded-md bg-black/80 text-white text-[11px] font-bold flex items-center gap-1">
                      <Play className="w-2.5 h-2.5 fill-white" />
                      <span>Video</span>
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-md bg-black/80 text-white text-[11px] font-bold flex items-center gap-1">
                      <ImageIcon className="w-2.5 h-2.5" />
                      <span>Photo</span>
                    </span>
                  )}
                </div>

                {/* Inspect / Preview Button */}
                {items[0]?.thumbnail && (
                  <button
                    type="button"
                    onClick={() => setPreviewMedia({
                      type: items[0].kind,
                      url: items[0].thumbnail
                    })}
                    className="absolute bottom-2 right-2 p-2 rounded-lg bg-black/70 hover:bg-black text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Expand preview"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Quality Selector & Download Button */}
              <div className="md:col-span-7 flex flex-col justify-between space-y-4">
                <div>
                  <h3 className="text-xs uppercase font-extrabold tracking-wider text-[var(--text-muted)] mb-3">
                    Available Qualities & Formats
                  </h3>

                  <div className="space-y-2">
                    {items[0]?.variants?.map((v, idx) => {
                      const isSelected = selectedVariantIdx === idx;
                      return (
                        <button
                          key={v.id || idx}
                          type="button"
                          onClick={() => setSelectedVariantIdx(idx)}
                          className={`w-full flex items-center justify-between p-3 rounded-xl border text-left transition-all ${
                            isSelected
                              ? 'bg-[var(--primary)] text-[var(--on-primary)] border-[var(--border-strong)] shadow-sm'
                              : 'bg-[var(--surface)] text-[var(--text)] border-[var(--border)] hover:border-[var(--text-muted)]'
                          }`}
                        >
                          <div className="flex items-center gap-2.5">
                            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                              isSelected ? 'border-[var(--on-primary)]' : 'border-[var(--border)]'
                            }`}>
                              {isSelected && <div className="w-2 h-2 rounded-full bg-[var(--on-primary)]" />}
                            </div>
                            <div>
                              <div className="font-bold text-sm">
                                {v.quality || (v.height ? `${v.height}p` : 'Standard')}
                              </div>
                              <div className={`text-xs ${isSelected ? 'opacity-80' : 'text-[var(--text-muted)]'}`}>
                                {v.ext.toUpperCase()} • {v.kind === 'video' ? 'Full Audio Included' : 'High Resolution'}
                              </div>
                            </div>
                          </div>

                          <div className="text-xs font-mono font-semibold">
                            {idx === 0 ? 'Best' : ''}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Primary Download Button */}
                <button
                  type="button"
                  onClick={() => {
                    const activeVariant = items[0]?.variants[selectedVariantIdx] || items[0]?.variants[0];
                    if (activeVariant) {
                      triggerDownload(activeVariant.downloadUrl);
                    }
                  }}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-bold text-base bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 active:scale-[0.99] transition-all shadow-[var(--shadow-1)]"
                >
                  <Download className="w-5 h-5" />
                  <span>Download {items[0]?.variants[selectedVariantIdx]?.quality || 'File'}</span>
                </button>
              </div>
            </div>
          ) : (
            /* Multi-Item / Carousel Grid View (Twitter 4-Image & Instagram Album) */
            <div className="space-y-6">
              
              {/* Batch Actions Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)]">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="select-all"
                    checked={selectedItems.length === items.length}
                    onChange={() => {
                      if (selectedItems.length === items.length) {
                        setSelectedItems([]);
                      } else {
                        setSelectedItems(items.map((_, i) => i));
                      }
                    }}
                    className="w-4 h-4 rounded accent-[var(--primary)]"
                  />
                  <label htmlFor="select-all" className="text-xs font-bold text-[var(--text)] cursor-pointer">
                    Select All ({selectedItems.length}/{items.length})
                  </label>
                </div>

                <button
                  type="button"
                  onClick={handleDownloadAll}
                  disabled={selectedItems.length === 0 || isDownloadingAll}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{isDownloadingAll ? 'Downloading...' : `Download Selected (${selectedItems.length})`}</span>
                </button>
              </div>

              {/* Items Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {items.map((item, idx) => {
                  const isChecked = selectedItems.includes(idx);
                  const bestVariant = item.variants[0];

                  return (
                    <div 
                      key={idx}
                      className={`relative rounded-xl overflow-hidden border-2 transition-all flex flex-col bg-[var(--surface)] ${
                        isChecked ? 'border-[var(--border-strong)]' : 'border-[var(--border)]'
                      }`}
                    >
                      {/* Selection Checkbox */}
                      <button
                        type="button"
                        onClick={() => toggleSelectItem(idx)}
                        className="absolute top-2 left-2 z-10 p-1 rounded-md bg-black/60 text-white hover:bg-black transition-colors"
                      >
                        <div className={`w-4 h-4 rounded border flex items-center justify-center ${
                          isChecked ? 'bg-white border-white' : 'border-white'
                        }`}>
                          {isChecked && <Check className="w-3 h-3 text-black stroke-[3]" />}
                        </div>
                      </button>

                      {/* Thumbnail with aspect ratio lock */}
                      <div className="relative aspect-square bg-[var(--bg-alt)] overflow-hidden group">
                        {item.thumbnail ? (
                          <img
                            src={item.thumbnail}
                            alt={`Item ${idx + 1}`}
                            className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-[var(--text-muted)]">
                            <ImageIcon className="w-8 h-8" />
                          </div>
                        )}

                        {/* Enlarge preview button */}
                        {item.thumbnail && (
                          <button
                            type="button"
                            onClick={() => setPreviewMedia({ type: item.kind, url: item.thumbnail })}
                            className="absolute bottom-2 right-2 p-1.5 rounded-lg bg-black/70 hover:bg-black text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Expand preview"
                          >
                            <Maximize2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>

                      {/* Item Bottom Bar */}
                      <div className="p-2.5 flex items-center justify-between border-t border-[var(--border)] text-xs">
                        <span className="font-bold text-[var(--text)]">
                          #{idx + 1} • {bestVariant?.quality || bestVariant?.ext.toUpperCase()}
                        </span>

                        <button
                          type="button"
                          onClick={() => triggerDownload(bestVariant?.downloadUrl)}
                          className="p-1.5 rounded-md hover:bg-[var(--bg-alt)] text-[var(--text)] transition-colors"
                          title="Download this item"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Card Footer: Reset / Download Another */}
        <div className="p-4 bg-[var(--bg-alt)] border-t border-[var(--border)] flex justify-between items-center text-xs text-[var(--text-muted)]">
          <span>OVD Signed Proxy • High-Speed Transfer</span>
          {onReset && (
            <button
              type="button"
              onClick={onReset}
              className="font-bold text-[var(--text)] hover:underline"
            >
              Download Another Link →
            </button>
          )}
        </div>
      </div>

      {/* Media Preview Modal */}
      {previewMedia && (
        <div 
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setPreviewMedia(null)}
        >
          <div 
            className="relative max-w-3xl max-h-[90vh] bg-[var(--surface)] border border-[var(--border)] rounded-2xl overflow-hidden shadow-2xl p-2"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setPreviewMedia(null)}
              className="absolute top-4 right-4 z-10 p-2 rounded-full bg-black/70 text-white hover:bg-black transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <img 
              src={previewMedia.url} 
              alt="Media Preview" 
              className="max-h-[80vh] w-auto mx-auto object-contain rounded-lg"
            />
          </div>
        </div>
      )}
    </section>
  );
}
