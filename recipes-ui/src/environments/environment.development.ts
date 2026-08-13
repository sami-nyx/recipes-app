export const environment = {
  production: false,
  apiUrl: 'localhost',
  apiPort: '5003',
  get fullApiUrl(): string {
    return `${this.apiUrl}:${this.apiPort}/api`;
  }
};