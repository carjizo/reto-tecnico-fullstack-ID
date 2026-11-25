import { LowerCasePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Alert, NewAlert, Severity } from './alert.model';
import { AlertService } from './alert.service';

const API_KEY_STORAGE_KEY = 'alerts.apiKey';

@Component({
  selector: 'app-root',
  imports: [FormsModule, LowerCasePipe],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly alertService = inject(AlertService);

  // Datos del formulario
  orderId = '';
  apiKey = this.readStoredApiKey();
  severityFilter: Severity | '' = '';
  newAlert: NewAlert = { severity: 'LOW', message: '', source: '' };

  readonly severities: Severity[] = ['LOW', 'MEDIUM', 'HIGH'];

  // Estado de la pantalla
  readonly alerts = signal<Alert[]>([]);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly searched = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  onApiKeyChange(): void {
    try {
      sessionStorage.setItem(API_KEY_STORAGE_KEY, this.apiKey);
    } catch {
      // sessionStorage puede no estar disponible; la clave solo vive en memoria.
    }
  }

  search(): void {
    const orderId = this.orderId.trim();
    if (!orderId || !this.apiKey) {
      this.error.set('Ingresa el orderId y la API key.');
      return;
    }

    this.error.set(null);
    this.loading.set(true);
    this.alertService.list(orderId, this.apiKey, this.severityFilter).subscribe({
      next: (alerts) => {
        this.alerts.set(alerts);
        this.searched.set(true);
        this.loading.set(false);
      },
      error: (err: unknown) => {
        this.alerts.set([]);
        this.error.set(toUserMessage(err));
        this.loading.set(false);
      },
    });
  }

  create(): void {
    const orderId = this.orderId.trim();
    if (!orderId || !this.apiKey) {
      this.error.set('Ingresa el orderId y la API key.');
      return;
    }
    if (!this.newAlert.message.trim() || !this.newAlert.source.trim()) {
      this.error.set('El mensaje y el origen son obligatorios.');
      return;
    }

    this.error.set(null);
    this.success.set(null);
    this.saving.set(true);
    this.alertService.create(orderId, this.apiKey, this.newAlert).subscribe({
      next: () => {
        this.saving.set(false);
        this.success.set('Alerta registrada.');
        this.newAlert = { severity: 'LOW', message: '', source: '' };
        this.search();
      },
      error: (err: unknown) => {
        this.saving.set(false);
        this.error.set(toUserMessage(err));
      },
    });
  }

  private readStoredApiKey(): string {
    try {
      return sessionStorage.getItem(API_KEY_STORAGE_KEY) ?? '';
    } catch {
      return '';
    }
  }
}

/** Convierte un error HTTP en un mensaje claro para el usuario. */
function toUserMessage(err: unknown): string {
  if (err instanceof HttpErrorResponse) {
    // 0: sin respuesta. 502, 503 y 504: el proxy o la API no pudo alcanzar el servicio.
    if ([0, 502, 503, 504].includes(err.status)) {
      return 'No se pudo conectar con la API. Revisa tu conexión.';
    }
    if (err.status === 401) {
      return 'API key inválida o ausente.';
    }
    if (err.status === 400) {
      return err.error?.error ?? 'Los datos no son válidos.';
    }
  }
  return 'Ocurrió un error inesperado. Intenta de nuevo.';
}
