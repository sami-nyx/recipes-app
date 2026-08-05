export const environment = {
  production: false,
  apiUrl: 'http://localhost',
  apiPort: '5001',
  get fullApiUrl(): string {
    return `${this.apiUrl}:${this.apiPort}/api`;
  }
};