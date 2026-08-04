const fs = require('fs');
const path = require('path');

// Target file to overwrite during CI build
const targetPath = path.join(__dirname, '../src/environments/environment.prod.ts');

// Fallbacks are provided for safety if variables aren't present
const apiUrl = process.env.API_URL || 'http://localhost';
const apiPort = process.env.API_PORT || '5000';

const environmentFileContent = `export const environment = {
  production: true,
  apiUrl: '${apiUrl}',
  apiPort: '${apiPort}',
  get fullApiUrl(): string {
    return this.apiPort ? \`\${this.apiUrl}:\${this.apiPort}/api\` : \`\${this.apiUrl}/api\`;
  }
};
`;

// Write/Overwrite the environment.prod.ts file
fs.writeFile(targetPath, environmentFileContent, (err) => {
  if (err) {
    console.error('Error writing environment configuration file:', err);
    process.exit(1);
  }
  console.log(`✅ Successfully generated environment.prod.ts with API_URL: ${apiUrl}:${apiPort}`);
});