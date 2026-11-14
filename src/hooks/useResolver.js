import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { resolveMedia } from '../utils/resolveMedia.js';
import { extractIncomingUrl } from '../utils/extractIncomingUrl.js';

/** Shared state machine for every downloader page: paste -> resolve -> result. */
export default function useResolver() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [errorCode, setErrorCode] = useState(null);
  const [retryable, setRetryable] = useState(true);
  const [data, setData] = useState(null);
  const resultRef = useRef(null);
  const reqRef = useRef(0);
  const abortRef = useRef(null);
  const lastIncoming = useRef('');
  const location = useLocation();

  const fetchMedia = useCallback(async (override) => {
    const target = (typeof override === 'string' && override.trim()) ? override.trim() : url.trim();
    if (!target) {
      setError('Paste a link to get started.');
      setErrorCode('URL_MISSING');
      return;
    }
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const myReq = ++reqRef.current;

    setLoading(true);
    setError('');
    setErrorCode(null);
    setData(null);
    try {
      const result = await resolveMedia(target, { signal: controller.signal });
      if (myReq !== reqRef.current || result.aborted) return;
      if (result.ok && result.data) {
        setData(result.data);
        requestAnimationFrame(() => {
          resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      } else {
        setErrorCode(result.code || null);
        setRetryable(result.retryable !== false);
        setError(result.error || 'Something went wrong. Please try again.');
      }
    } catch (e) {
      if (myReq === reqRef.current) setError('Connection interrupted. Please try again.');
    } finally {
      if (myReq === reqRef.current) setLoading(false);
    }
  }, [url]);

  // ?url= / ?link= / ?q= / Web-Share-Target links start a lookup automatically
  useEffect(() => {
    const incoming = extractIncomingUrl(location);
    if (incoming && incoming !== lastIncoming.current) {
      lastIncoming.current = incoming;
      setUrl(incoming);
      fetchMedia(incoming);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search, location.hash, location.pathname]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    reqRef.current++;
    setUrl('');
    setError('');
    setErrorCode(null);
    setData(null);
    setLoading(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const changeUrl = useCallback((v) => { setUrl(v); setError((e) => (e ? '' : e)); }, []);

  return { url, setUrl: changeUrl, loading, error, errorCode, retryable, data, fetchMedia, reset, resultRef };
}
