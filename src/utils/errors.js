export const ErrorCode = {
  // Master Prompt v3 Error Codes
  PRIVATE_CONTENT: 'PRIVATE_CONTENT',
  NOT_FOUND: 'NOT_FOUND',
  LOGIN_REQUIRED: 'LOGIN_REQUIRED',
  UNSUPPORTED_URL: 'UNSUPPORTED_URL',
  RATE_LIMITED: 'RATE_LIMITED',
  GEO_BLOCKED: 'GEO_BLOCKED',
  EXTRACTION_FAILED: 'EXTRACTION_FAILED',

  // Legacy Codes (Backward Compatibility)
  URL_MISSING: 'URL_MISSING',
  URL_INVALID: 'URL_INVALID',
  PLATFORM_UNSUPPORTED: 'UNSUPPORTED_URL',
  NO_MEDIA: 'NOT_FOUND',
  PRIVATE_OR_RESTRICTED: 'PRIVATE_CONTENT',
  UPSTREAM_FAILED: 'EXTRACTION_FAILED',
  TIMEOUT: 'EXTRACTION_FAILED',
  INTERNAL: 'EXTRACTION_FAILED'
};

export const ERROR_DETAILS = {
  PRIVATE_CONTENT: {
    message: 'This media is private or restricted by the creator.',
    retryable: false
  },
  NOT_FOUND: {
    message: 'This post or video was deleted or does not exist.',
    retryable: false
  },
  LOGIN_REQUIRED: {
    message: 'This content requires account login (such as private stories or groups).',
    retryable: false
  },
  UNSUPPORTED_URL: {
    message: 'This website is not currently supported. Try Twitter, YouTube, Instagram, TikTok, Facebook, Reddit, Pinterest, or Threads.',
    retryable: false
  },
  RATE_LIMITED: {
    message: 'Upstream rate limit reached. Please wait a minute and try again.',
    retryable: true
  },
  GEO_BLOCKED: {
    message: 'This media is geographically restricted and unavailable in our server region.',
    retryable: false
  },
  EXTRACTION_FAILED: {
    message: 'Could not extract media from this URL. Please verify the link and try again.',
    retryable: true
  },
  URL_MISSING: {
    message: 'Paste a link to get started.',
    retryable: true
  },
  URL_INVALID: {
    message: "That doesn't look like a valid web link. Please check the URL.",
    retryable: true
  }
};

export function getErrorMessage(code, fallbackMessage) {
  if (code && ERROR_DETAILS[code]) {
    return ERROR_DETAILS[code].message;
  }
  return fallbackMessage || ERROR_DETAILS.EXTRACTION_FAILED.message;
}

export function isRetryableError(code) {
  if (code && ERROR_DETAILS[code]) {
    return Boolean(ERROR_DETAILS[code].retryable);
  }
  return true;
}
