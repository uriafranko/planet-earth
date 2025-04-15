import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import { componentTagger } from 'lovable-tagger';
import fs from 'fs/promises';

/**
 * Recursively copies files from src to dest.
 */
async function copyDir(src: string, dest: string) {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  base: '/ui/',
  server: {
    host: '::',
    port: 8080,
  },
  plugins: [
    react(),
    mode === 'development' && componentTagger(),
    // Custom plugin to copy build output to ../eath-backend/app/frontend
    mode === 'production' && {
      name: 'copy-build-to-backend',
      closeBundle: async () => {
        const outDir = path.resolve(__dirname, 'dist');
        const targetDir = path.resolve(__dirname, '../earth-backend/app/ui');
        try {
          await copyDir(outDir, targetDir);
          console.log(`Copied build to ${targetDir}`);
        } catch (err) {
          console.error('Failed to copy build output:', err);
        }
      },
    },
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
}));
