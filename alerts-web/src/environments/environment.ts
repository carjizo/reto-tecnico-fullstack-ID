// Ruta relativa: en desarrollo la resuelve el proxy de ng serve (proxy.conf.json),
// así el navegador no hace peticiones cross-origin hacia LocalStack.
export const environment = {
  apiBaseUrl: '/api/v1/orders',
};
