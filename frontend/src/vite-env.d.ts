/// <reference types="vite/client" />

/**
 * Extend Vite's ImportMeta interface to include custom environment variables
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
