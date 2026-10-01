import { HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';
import { SendResult } from './models';

/**
 * Sends a chat message and reads the tutor's reply as it is written (server-sent events over a POST).
 * Errors come back as HttpErrorResponse, so screens handle them like any other request.
 */
@Injectable({ providedIn: 'root' })
export class ChatStreamService {
  private api = inject(ApiService);
  private auth = inject(AuthService);

  async send(conversationId: number, text: string, onReply: (textSoFar: string) => void): Promise<SendResult> {
    let response = await this.post(conversationId, text);
    if (response.status === 401) {
      // The access token lives 15 minutes: refresh once, as the HTTP interceptor does for other requests.
      try {
        await firstValueFrom(this.api.refresh());
      } catch (e) {
        await this.auth.clear(); // the session is gone: back to the login screen
        throw e;
      }
      response = await this.post(conversationId, text);
    }
    if (!response.ok || !response.body) throw await this.error(response);

    const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += value;
      let cut: number;
      while ((cut = buffer.indexOf('\n\n')) >= 0) {
        const event = parse(buffer.slice(0, cut));
        buffer = buffer.slice(cut + 2);
        if (!event) continue;
        if (event.name === 'reply') onReply(event.data['text'] as string);
        else if (event.name === 'done') return event.data as unknown as SendResult;
        else if (event.name === 'error') {
          throw new HttpErrorResponse({ status: Number(event.data['status']) || 503, error: event.data });
        }
      }
    }
    // The connection closed before the tutor finished.
    throw new HttpErrorResponse({ status: 0, error: null });
  }

  private post(id: number, text: string): Promise<Response> {
    return fetch(`/api/chat/conversations/${id}/messages/stream/`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
        // JSON for errors found before the stream starts, events once it does.
        Accept: 'application/json, text/event-stream',
      },
      body: JSON.stringify({ text }),
    }).catch(() => {
      throw new HttpErrorResponse({ status: 0, error: null });
    });
  }

  private async error(response: Response): Promise<HttpErrorResponse> {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      /* not JSON */
    }
    const headers = new HttpHeaders({ 'Retry-After': response.headers.get('Retry-After') ?? '' });
    return new HttpErrorResponse({ status: response.status, error: body, headers });
  }
}

function parse(chunk: string): { name: string; data: Record<string, unknown> } | null {
  let name = 'message';
  let data = '';
  for (const line of chunk.split('\n')) {
    if (line.startsWith('event: ')) name = line.slice(7);
    else if (line.startsWith('data: ')) data += line.slice(6);
  }
  try {
    return { name, data: JSON.parse(data) };
  } catch {
    return null;
  }
}

function csrfToken(): string {
  return document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)?.[1] ?? '';
}
