// Single source of truth for what the UI accepts. Keep in sync with backend/uploads/services.py.
export const MODALITIES = {
  document: { label: 'Documents', hint: 'PDF, TXT, DOCX', exts: ['.pdf', '.txt', '.docx'], maxMB: 25 },
  image:    { label: 'Images',    hint: 'PNG, JPG, WEBP', exts: ['.png', '.jpg', '.jpeg', '.webp'], maxMB: 15 },
  audio:    { label: 'Audio',     hint: 'MP3, WAV, M4A, OGG', exts: ['.mp3', '.wav', '.m4a', '.ogg'], maxMB: 100 },
};

export const ACCEPT = Object.values(MODALITIES).flatMap((m) => m.exts).join(',');

export const extOf = (name) => {
  const i = name.lastIndexOf('.');
  return i === -1 ? '' : name.slice(i).toLowerCase();
};

export const modalityOf = (name) =>
  Object.keys(MODALITIES).find((k) => MODALITIES[k].exts.includes(extOf(name))) ?? null;

export const prettySize = (bytes) =>
  bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
