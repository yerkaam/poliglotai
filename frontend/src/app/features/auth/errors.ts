import { HttpErrorResponse } from '@angular/common/http';

/** Turns a DRF error body into { field: message } plus a general message. */
export function apiErrors(error: unknown): { general: string; fields: Record<string, string> } {
  const fallback = $localize`Байланыс қатесі. Қайталап көріңіз.`;
  if (!(error instanceof HttpErrorResponse) || typeof error.error !== 'object' || error.error === null) {
    return { general: fallback, fields: {} };
  }
  const fields: Record<string, string> = {};
  let general = '';
  for (const [key, value] of Object.entries(error.error as Record<string, unknown>)) {
    const message = Array.isArray(value) ? String(value[0]) : String(value);
    if (key === 'detail' || key === 'non_field_errors') general = message;
    else if (key !== 'code' && key !== 'retry_after') fields[key] = message;
  }
  if (!general && !Object.keys(fields).length) general = fallback;
  return { general, fields };
}
