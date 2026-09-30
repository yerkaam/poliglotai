import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { Profile, User } from './models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(ApiService);
  private router = inject(Router);

  readonly user = signal<User | null>(null);
  readonly isLoggedIn = computed(() => this.user() !== null);

  /** Runs once at start-up: gets the CSRF cookie, then asks who is logged in. */
  async init(): Promise<void> {
    try {
      await firstValueFrom(this.api.csrf());
      this.user.set(await firstValueFrom(this.api.me()));
    } catch {
      this.user.set(null);
    }
  }

  async login(email: string, password: string, remember: boolean) {
    this.user.set(await firstValueFrom(this.api.login(email, password, remember)));
    await this.offerToSavePassword(email, password);
  }

  async register(data: { name: string; email: string; password: string; password2: string; accept_terms: boolean }) {
    this.user.set(await firstValueFrom(this.api.register(data)));
    await this.offerToSavePassword(data.email, data.password, data.name);
  }

  async verifyEmail(code: string) {
    this.user.set(await firstValueFrom(this.api.verifyEmail(code)));
  }

  async updateProfile(data: Partial<Profile>) {
    this.user.set(await firstValueFrom(this.api.updateProfile(data)));
  }

  /** AUTH-13: the token cookies are removed and the learner lands on the login screen. */
  async logout() {
    try {
      await firstValueFrom(this.api.logout());
    } finally {
      await this.clear();
    }
  }

  /**
   * The page never reloads after login, so browsers do not always notice it. Where the Credential
   * Management API exists (Chrome, Edge), hand the login to the password manager explicitly.
   */
  private async offerToSavePassword(email: string, password: string, name?: string) {
    const PasswordCredentialCtor = (window as unknown as { PasswordCredential?: new (data: object) => Credential })
      .PasswordCredential;
    if (!PasswordCredentialCtor || !navigator.credentials?.store) return;
    try {
      await navigator.credentials.store(new PasswordCredentialCtor({ id: email, password, name: name ?? email }));
    } catch {
      /* the browser or the user declined */
    }
  }

  clear() {
    this.user.set(null);
    return this.router.navigate(['/login']);
  }
}
