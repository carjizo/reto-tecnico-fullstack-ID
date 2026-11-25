import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../environments/environment';
import { Alert, NewAlert, Severity } from './alert.model';

/** Llamadas a la API de alertas. No guarda estado: solo habla con el backend. */
@Injectable({ providedIn: 'root' })
export class AlertService {
  private readonly http = inject(HttpClient);

  list(orderId: string, apiKey: string, severity: Severity | ''): Observable<Alert[]> {
    let params = new HttpParams();
    if (severity) {
      params = params.set('severity', severity);
    }
    return this.http.get<Alert[]>(this.alertsUrl(orderId), {
      headers: this.authHeaders(apiKey),
      params,
    });
  }

  create(orderId: string, apiKey: string, alert: NewAlert): Observable<Alert> {
    return this.http.post<Alert>(this.alertsUrl(orderId), alert, {
      headers: this.authHeaders(apiKey),
    });
  }

  private alertsUrl(orderId: string): string {
    return `${environment.apiBaseUrl}/${encodeURIComponent(orderId)}/alerts`;
  }

  private authHeaders(apiKey: string): HttpHeaders {
    return new HttpHeaders({ 'X-Api-Key': apiKey });
  }
}
