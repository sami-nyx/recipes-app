export const environment = {
  production: false,
  apiUrl: 'http://localhost',
  apiPort: '5000',
  get fullApiUrl(): string {
    return `${this.apiUrl}:${this.apiPort}/api`;
  }
};