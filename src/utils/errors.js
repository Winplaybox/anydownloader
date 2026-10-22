export const ErrorCode = {
  URL_MISSING: 'URL_MISSING',
  URL_INVALID: 'URL_INVALID',
  PLATFORM_UNSUPPORTED: 'PLATFORM_UNSUPPORTED',
  NO_MEDIA: 'NO_MEDIA',
  NOT_FOUND: 'NOT_FOUND',
  PRIVATE_OR_RESTRICTED: 'PRIVATE_OR_RESTRICTED',
  RATE_LIMITED: 'RATE_LIMITED',
  UPSTREAM_FAILED: 'UPSTREAM_FAILED',
  TIMEOUT: 'TIMEOUT',
  INTERNAL: 'INTERNAL'
};

export const ERROR_MESSAGES = {
  URL_MISSING: 'Paste a link to get started.',
  URL_INVALID: "That doesn't look like a valid link.",
  PLATFORM_UNSUPPORTED: "This site isn't supported yet. Supported: X, YouTube, Facebook, Instagram, TikTok.",
  NO_MEDIA: 'This post has no video or image to download.',
  NOT_FOUND: "This post was deleted or doesn't exist.",
  PRIVATE_OR_RESTRICTED: 'This content is private, age-restricted, or needs login.',
  RATE_LIMITED: 'Too many requests. Try again in a minute.',
  UPSTREAM_FAILED: "The platform didn't respond. Try again.",
  TIMEOUT: 'That took too long. Try again.',
  INTERNAL: 'Something went wrong on our side.'
};

export function getErrorMessage(code, fallbackMessage) {
  if (code && ERROR_MESSAGES[code]) {
    return ERROR_MESSAGES[code];
  }
  return fallbackMessage || ERROR_MESSAGES.INTERNAL;
}
