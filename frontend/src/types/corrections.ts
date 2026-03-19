/**
 * Type definitions for the text correction application
 */

export interface Correction {
  type: 'grammar' | 'spelling' | 'style' | 'tone' | 'rephrasing';
  original_text: string;
  suggested_text: string;
  explanation?: string;
  start_position?: number;
  end_position?: number;
}

export interface StreamChunk {
  type: 'chunk' | 'complete' | 'error' | 'start' | 'close';
  content?: string;
  chunk_number?: number;
  total_chunks?: number;
  request_id?: string;
  error?: string;
  message?: string;
}

export interface CorrectionRequest {
  text: string;
  request_id?: string;
}
