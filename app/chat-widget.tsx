'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';

type ChatTurn = {
  role: 'user' | 'assistant';
  content: string;
  temporary?: boolean;
};

type ChatResponse = {
  answer: string;
};

function isChatResponse(value: unknown): value is ChatResponse {
  if (!value || typeof value !== 'object') return false;
  const response = value as Record<string, unknown>;
  return typeof response.answer === 'string';
}

function getErrorMessage(value: unknown): string {
  if (value instanceof Error) return value.message;
  return 'The advisor could not answer this request. Please try again.';
}

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const logRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const openFromHash = () => {
      if (window.location.hash === '#assistant') setIsOpen(true);
    };
    openFromHash();
    window.addEventListener('hashchange', openFromHash);
    return () => window.removeEventListener('hashchange', openFromHash);
  }, []);

  useEffect(() => {
    if (isOpen) inputRef.current?.focus({ preventScroll: true });
  }, [isOpen]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [isLoading, messages]);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || isLoading) return;

    const history = messages
      .filter((message) => !message.temporary)
      .slice(-6)
      .map(({ role, content }) => ({ role, content }));

    setMessages((current) => [
      ...current.filter((message) => !message.temporary),
      { role: 'user', content: question, temporary: true },
    ]);
    setDraft('');
    setErrorMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: question, history }),
      });
      const data: unknown = await response.json();

      if (!response.ok) {
        const detail =
          data && typeof data === 'object' && 'detail' in data
            ? (data as { detail?: unknown }).detail
            : undefined;
        throw new Error(
          typeof detail === 'string'
            ? detail
            : 'The advisor could not answer this request. Please try again.',
        );
      }
      if (!isChatResponse(data)) {
        throw new Error('The advisor returned an unexpected response.');
      }

      setMessages((current) => [
        ...current.filter((message) => !message.temporary),
        { role: 'user', content: question },
        { role: 'assistant', content: data.answer },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current.filter((message) => !message.temporary),
        { role: 'user', content: question, temporary: true },
      ]);
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="assistant-widget" id="assistant">
      {isOpen ? (
        <section className="assistant-panel" aria-label="Nokshi Legal Advisor">
          <header className="assistant-header">
            <span className="assistant-live-dot" aria-hidden="true" />
            <div>
              <strong>Nokshi Legal Advisor</strong>
            </div>
            <button
              className="assistant-close"
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label="Close advisor"
              title="Close advisor"
            >
              ×
            </button>
          </header>
          <div className="assistant-log" ref={logRef} aria-live="polite">
            {messages.length === 0 && (
              <article className="assistant-message assistant-message-bot">
                Ask a question about Nokshi Threads.
              </article>
            )}
            {messages.map((message, index) => (
              <article
                className={`assistant-message ${
                  message.role === 'user'
                    ? 'assistant-message-user'
                    : 'assistant-message-bot'
                }`}
                key={`${message.role}-${index}`}
              >
                <p>{message.content}</p>
              </article>
            ))}
            {isLoading && (
              <article
                className="assistant-message assistant-message-bot assistant-typing"
                role="status"
                aria-label="Waiting for a response"
              >
                <span />
                <span />
                <span />
              </article>
            )}
            {errorMessage && (
              <p className="assistant-error" role="alert">
                {errorMessage}
              </p>
            )}
          </div>
          <form className="assistant-form" onSubmit={sendMessage}>
            <label className="sr-only" htmlFor="assistant-question">
              Ask Nokshi Legal Advisor
            </label>
            <textarea
              id="assistant-question"
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              maxLength={1500}
              rows={2}
              placeholder="Ask about the Nokshi case or its sources…"
              disabled={isLoading}
            />
            <button
              className="btn primary"
              type="submit"
              disabled={isLoading || !draft.trim()}
            >
              {isLoading ? 'Sending…' : 'Ask'}
            </button>
          </form>
        </section>
      ) : (
        <button
          className="assistant-launcher"
          type="button"
          onClick={() => setIsOpen(true)}
          aria-expanded={false}
          aria-controls="assistant"
        >
          <span aria-hidden="true">✦</span>
          Ask Nokshi
          <span className="assistant-live-dot" aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
