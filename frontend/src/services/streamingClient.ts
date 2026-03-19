/**
 * Streaming API Client for text corrections using Server-Sent Events.
 * 
 * This service handles communication with the FastAPI backend streaming endpoint,
 * manages SSE connections, and provides callbacks for real-time correction chunks.
 */

import type { CorrectionRequest, StreamChunk } from '../types/corrections';

type ChunkCallback = (chunk: StreamChunk) => void;
type ErrorCallback = (error: Error) => void;
type CompleteCallback = () => void;

interface StreamCallbacks {
  onChunk: ChunkCallback;
  onError?: ErrorCallback;
  onComplete?: CompleteCallback;
}

class StreamingAPIClient {
  private baseURL: string;
  private activeConnection: AbortController | null = null;

  constructor() {
    // Use environment variable or fallback to default
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  }

  /**
   * Stream text corrections from the backend using Server-Sent Events.
   * 
   * @param request - The correction request containing text to analyze
   * @param callbacks - Callbacks for handling stream events
   * @returns AbortController for cancelling the stream
   */
  async streamCorrections(
    request: CorrectionRequest,
    callbacks: StreamCallbacks
  ): Promise<AbortController> {
    // Cancel any existing connection
    if (this.activeConnection) {
      this.cancelStream();
    }

    // Create new abort controller for this request
    const abortController = new AbortController();
    this.activeConnection = abortController;

    // Start streaming in background - don't await
    this.startStreamProcessing(request, callbacks, abortController);

    // Return controller immediately so UI isn't blocked
    return abortController;
  }

  /**
   * Start stream processing in background (non-blocking)
   */
  private async startStreamProcessing(
    request: CorrectionRequest,
    callbacks: StreamCallbacks,
    abortController: AbortController
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseURL}/api/corrections/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Process Server-Sent Events stream
      await this.processSSEStream(response, callbacks, abortController);

    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          console.log('Stream cancelled by user');
        } else {
          console.error('Stream error:', error);
          callbacks.onError?.(error);
        }
      }
    } finally {
      // Clean up active connection reference
      if (this.activeConnection === abortController) {
        this.activeConnection = null;
      }
    }
  }

  /**
   * Process Server-Sent Events stream from the response.
   * 
   * @param response - Fetch response with SSE stream
   * @param callbacks - Callbacks for handling events
   * @param abortController - Controller for cancellation
   */
  private async processSSEStream(
    response: Response,
    callbacks: StreamCallbacks,
    abortController: AbortController
  ): Promise<void> {
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (!abortController.signal.aborted) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        let currentEvent = '';
        let currentData = '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim();
          } else if (line.startsWith('data:')) {
            currentData = line.substring(5).trim();
          } else if (line === '') {
            // Empty line signals end of message
            if (currentData) {
              this.handleSSEMessage(currentEvent, currentData, callbacks);
              currentEvent = '';
              currentData = '';
            }
          }
        }
      }

      // Stream completed successfully
      callbacks.onComplete?.();

    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        throw error;
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Handle individual SSE message.
   * 
   * @param event - Event type (start, chunk, complete, error, close)
   * @param data - JSON data payload
   * @param callbacks - Callbacks for handling the message
   */
  private handleSSEMessage(
    event: string,
    data: string,
    callbacks: StreamCallbacks
  ): void {
    try {
      const chunk: StreamChunk = JSON.parse(data);

      // Invoke appropriate callback based on event type
      switch (event) {
        case 'start':
          console.log('Stream started:', chunk.request_id);
          break;

        case 'chunk':
          callbacks.onChunk(chunk);
          break;

        case 'complete':
          console.log('Stream completed:', chunk.total_chunks, 'chunks');
          callbacks.onChunk(chunk);
          break;

        case 'error':
          console.error('Stream error:', chunk.error);
          if (callbacks.onError) {
            callbacks.onError(new Error(chunk.error || 'Unknown stream error'));
          }
          callbacks.onChunk(chunk); // Also send error as chunk for UI handling
          break;

        case 'close':
          console.log('Stream closed');
          break;

        default:
          console.warn('Unknown event type:', event);
      }
    } catch (error) {
      console.error('Failed to parse SSE message:', data, error);
      callbacks.onError?.(new Error('Failed to parse server response'));
    }
  }

  /**
   * Cancel the active stream connection.
   */
  cancelStream(): void {
    if (this.activeConnection) {
      console.log('Cancelling active stream...');
      this.activeConnection.abort();
      this.activeConnection = null;
    }
  }

  /**
   * Check if there's an active stream connection.
   */
  hasActiveStream(): boolean {
    return this.activeConnection !== null;
  }
}

// Export singleton instance
export const streamingAPIClient = new StreamingAPIClient();
export default streamingAPIClient;
