export type Severity = 'LOW' | 'MEDIUM' | 'HIGH';

export interface Alert {
  orderId: string;
  alertId: string;
  severity: Severity;
  message: string;
  source: string;
  createdAt: string;
}

export interface NewAlert {
  severity: Severity;
  message: string;
  source: string;
}
