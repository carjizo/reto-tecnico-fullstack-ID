import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { App } from './app';

describe('App', () => {
  let fixture: ComponentFixture<App>;
  let http: HttpTestingController;

  beforeEach(async () => {
    sessionStorage.clear();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(App);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  function text(): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  it('pide orderId y API key antes de consultar', () => {
    fixture.componentInstance.search();
    fixture.detectChanges();

    expect(text()).toContain('Ingresa el orderId y la API key.');
    http.expectNone(() => true);
  });

  it('muestra el estado de carga mientras espera la respuesta', () => {
    const app = fixture.componentInstance;
    app.orderId = 'ORD-1001';
    app.apiKey = 'clave-prueba';
    app.search();
    fixture.detectChanges();

    expect(text()).toContain('Cargando');

    http.expectOne((r) => r.url === '/api/v1/orders/ORD-1001/alerts').flush([]);
    fixture.detectChanges();
  });

  it('muestra el mensaje de lista vacía cuando la orden no tiene alertas', () => {
    const app = fixture.componentInstance;
    app.orderId = 'ORD-1001';
    app.apiKey = 'clave-prueba';
    app.search();

    http.expectOne((r) => r.url === '/api/v1/orders/ORD-1001/alerts').flush([]);
    fixture.detectChanges();

    expect(text()).toContain('Esta orden no tiene alertas');
  });

  it('muestra el error cuando la API key es inválida (401)', () => {
    const app = fixture.componentInstance;
    app.orderId = 'ORD-1001';
    app.apiKey = 'clave-incorrecta';
    app.search();

    http
      .expectOne((r) => r.url === '/api/v1/orders/ORD-1001/alerts')
      .flush({ error: 'API key inválida o ausente' }, { status: 401, statusText: 'Unauthorized' });
    fixture.detectChanges();

    expect(text()).toContain('API key inválida o ausente.');
  });

  it('muestra error de red cuando la API no responde (status 0)', () => {
    const app = fixture.componentInstance;
    app.orderId = 'ORD-1001';
    app.apiKey = 'clave-prueba';
    app.search();

    http
      .expectOne((r) => r.url === '/api/v1/orders/ORD-1001/alerts')
      .error(new ProgressEvent('error'), { status: 0, statusText: '' });
    fixture.detectChanges();

    expect(text()).toContain('No se pudo conectar con la API');
  });

  it('muestra mensaje de conexión cuando el servicio responde 504 (gateway timeout)', () => {
    const app = fixture.componentInstance;
    app.orderId = 'ORD-1001';
    app.apiKey = 'clave-prueba';
    app.search();

    http
      .expectOne((r) => r.url === '/api/v1/orders/ORD-1001/alerts')
      .flush({}, { status: 504, statusText: 'Gateway Timeout' });
    fixture.detectChanges();

    expect(text()).toContain('No se pudo conectar con la API');
  });

  it('muestra el mensaje de validación de la API al registrar una alerta inválida', () => {
    const app = fixture.componentInstance;
    app.orderId = 'ORD-1001';
    app.apiKey = 'clave-prueba';
    app.newAlert = { severity: 'LOW', message: 'Prueba', source: 'monitoring' };
    app.create();

    http
      .expectOne({ method: 'POST', url: '/api/v1/orders/ORD-1001/alerts' })
      .flush({ error: 'severity debe ser LOW, MEDIUM o HIGH' }, { status: 400, statusText: 'Bad Request' });
    fixture.detectChanges();

    expect(text()).toContain('severity debe ser LOW, MEDIUM o HIGH');
  });
});
