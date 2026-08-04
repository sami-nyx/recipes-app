export const environment = {
  production: true,
  apiUrl: '',
  apiPort: '',
  get fullApiUrl(): string {
    return this.apiPort ? `${this.apiUrl}:${this.apiPort}/api` : `${this.apiUrl}/api`;
  }
};