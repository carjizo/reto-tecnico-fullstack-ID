import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { Alert } from './alert.model';
import { AlertService } from './alert.service';

const sampleAlert: Alert = {
  orderId: 'ORD-1001',
  alertId: '2026-11-25T10:15:00.123Z#0b9c4f2e',
  severity: 'HIGH',
  message: 'Latencia alta en el pago',
  source: 'monitoring',
  createdAt: '2026-11-25T10:15:00.123Z',
};

describe('AlertService', () => {
  let service: AlertService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AlertService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lista alertas enviando la API key y el filtro de severidad', () => {
    let received: Alert[] = [];
    service.list('ORD-1001', 'clave-prueba', 'HIGH').subscribe((alerts) => (received = alerts));

    const req = http.expectOne((r) => r.url === '/api/v1/orders/ORD-1001/alerts');
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('X-Api-Key')).toBe('clave-prueba');
    expect(req.request.params.get('severity')).toBe('HIGH');
    req.flush([sampleAlert]);

    expect(received).toEqual([sampleAlert]);
  });

  it('lista sin filtro cuando la severidad está vacía', () => {
    service.list('ORD-1001', 'clave-prueba', '').subscribe();

    const req = http.expectOne((r) => r.url === '/api/v1/orders/ORD-1001/alerts');
    expect(req.request.params.has('severity')).toBe(false);
    req.flush([]);
  });

  it('crea una alerta con POST y el cuerpo indicado', () => {
    service.create('ORD-1001', 'clave-prueba', {
      severity: 'LOW',
      message: 'Reintento exitoso',
      source: 'worker',
    }).subscribe();

    const req = http.expectOne('/api/v1/orders/ORD-1001/alerts');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      severity: 'LOW',
      message: 'Reintento exitoso',
      source: 'worker',
    });
    req.flush(sampleAlert, { status: 201, statusText: 'Created' });
  });

  it('propaga el error 400 de validación de la API', () => {
    let error: HttpErrorResponse | undefined;
    service.create('ORD-1001', 'clave-prueba', {
      severity: 'LOW',
      message: '',
      source: 'worker',
    }).subscribe({ error: (e: HttpErrorResponse) => (error = e) });

    const req = http.expectOne('/api/v1/orders/ORD-1001/alerts');
    req.flush(
      { error: 'message es obligatorio' },
      { status: 400, statusText: 'Bad Request' },
    );

    expect(error?.status).toBe(400);
    expect(error?.error.error).toBe('message es obligatorio');
  });
});
