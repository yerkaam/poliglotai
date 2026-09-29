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
  }

  async register(data: { name: string; email: string; password: string; password2: string; accept_terms: boolean }) {
    this.user.set(await firstValueFrom(this.api.register(data)));
  }

  async updateProfile(data: Partial<Profile>) {
    this.user.set(await firstValueFrom(this.api.updateProfile(data)));
  }

  /** AUTH-13: the token cookies are removed and the learner lands on the login screen. */
  async logout() {
    try {
      await firstValueFrom(this.api.logout());
    } finally {
      this.clear();
    }
  }

  clear() {
    this.user.set(null);
    this.router.navigate(['/login']);
  }
}
