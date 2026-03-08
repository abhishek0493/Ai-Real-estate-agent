import { useState, useRef, useEffect, FormEvent } from "react";
import { useChat, Message } from "../hooks/useChat";

/* ── Chat Button (floating) ───────────────────────────────────── */

function ChatButton({ onClick, isOpen }: { onClick: () => void; isOpen: boolean }) {
  return (
    <button
      onClick={onClick}
      className="cw-fixed cw-bottom-6 cw-right-6 cw-w-14 cw-h-14 cw-rounded-full cw-bg-indigo-600 hover:cw-bg-indigo-500 cw-text-white cw-shadow-xl cw-shadow-indigo-500/30 cw-flex cw-items-center cw-justify-center cw-transition-all cw-duration-300 cw-z-[9999]"
      style={{ transform: isOpen ? "scale(0)" : "scale(1)" }}
      aria-label="Open chat"
    >
      <svg className="cw-w-6 cw-h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    </button>
  );
}

/* ── Message Bubble ───────────────────────────────────────────── */

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`cw-flex ${isUser ? "cw-justify-end" : "cw-justify-start"} cw-mb-3`}>
      <div
        className={`cw-max-w-[80%] cw-px-4 cw-py-2.5 cw-rounded-2xl cw-text-sm cw-leading-relaxed ${
          isUser
            ? "cw-bg-indigo-600 cw-text-white cw-rounded-br-md"
            : "cw-bg-gray-100 cw-text-gray-800 cw-rounded-bl-md"
        }`}
      >
        {msg.content}
      </div>
    </div>
  );
}

/* ── Typing Indicator ─────────────────────────────────────────── */

function TypingIndicator() {
  return (
    <div className="cw-flex cw-justify-start cw-mb-3">
      <div className="cw-bg-gray-100 cw-px-4 cw-py-3 cw-rounded-2xl cw-rounded-bl-md cw-flex cw-gap-1">
        <span className="cw-w-2 cw-h-2 cw-bg-gray-400 cw-rounded-full cw-animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="cw-w-2 cw-h-2 cw-bg-gray-400 cw-rounded-full cw-animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="cw-w-2 cw-h-2 cw-bg-gray-400 cw-rounded-full cw-animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
    </div>
  );
}

/* ── Chat Input ───────────────────────────────────────────────── */

function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  useEffect(() => {
    inputRef.current?.focus();
  }, [disabled]);

  return (
    <form onSubmit={handleSubmit} className="cw-flex cw-gap-2 cw-p-4 cw-border-t cw-border-gray-200">
      <input
        ref={inputRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type a message…"
        disabled={disabled}
        className="cw-flex-1 cw-px-4 cw-py-2.5 cw-bg-gray-50 cw-border cw-border-gray-200 cw-rounded-xl cw-text-sm cw-text-gray-800 cw-placeholder-gray-400 focus:cw-outline-none focus:cw-ring-2 focus:cw-ring-indigo-500 focus:cw-border-transparent disabled:cw-opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="cw-px-4 cw-py-2.5 cw-bg-indigo-600 hover:cw-bg-indigo-500 disabled:cw-bg-indigo-300 cw-text-white cw-rounded-xl cw-text-sm cw-font-medium cw-transition"
      >
        <svg className="cw-w-5 cw-h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </form>
  );
}

/* ── Chat Window ──────────────────────────────────────────────── */

function ChatWindow({ onClose }: { onClose: () => void }) {
  const { messages, loading, send, reset } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  return (
    <div
      className="cw-fixed cw-bottom-6 cw-right-6 cw-z-[9999] cw-flex cw-flex-col cw-bg-white cw-rounded-2xl cw-shadow-2xl cw-overflow-hidden cw-border cw-border-gray-200"
      style={{ width: 370, height: 520 }}
    >
      {/* Header */}
      <div className="cw-flex cw-items-center cw-justify-between cw-px-5 cw-py-4 cw-bg-indigo-600">
        <div className="cw-flex cw-items-center cw-gap-3">
          <div className="cw-w-9 cw-h-9 cw-rounded-full cw-bg-white/20 cw-flex cw-items-center cw-justify-center">
            <svg className="cw-w-5 cw-h-5 cw-text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          </div>
          <div>
            <p className="cw-text-white cw-font-semibold cw-text-sm">AI Property Assistant</p>
            <p className="cw-text-indigo-200 cw-text-xs">We help you find your dream home</p>
          </div>
        </div>
        <div className="cw-flex cw-gap-1">
          <button
            onClick={reset}
            className="cw-text-indigo-200 hover:cw-text-white cw-transition cw-p-1.5"
            title="New conversation"
          >
            <svg className="cw-w-4 cw-h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <button
            onClick={onClose}
            className="cw-text-indigo-200 hover:cw-text-white cw-transition cw-p-1.5"
            title="Close"
          >
            <svg className="cw-w-4 cw-h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="cw-flex-1 cw-overflow-y-auto cw-px-4 cw-py-4">
        {messages.length === 0 && (
          <div className="cw-text-center cw-py-8">
            <div className="cw-w-12 cw-h-12 cw-mx-auto cw-mb-3 cw-rounded-full cw-bg-indigo-50 cw-flex cw-items-center cw-justify-center">
              <svg className="cw-w-6 cw-h-6 cw-text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="cw-text-gray-600 cw-text-sm cw-font-medium">Hi there! 👋</p>
            <p className="cw-text-gray-400 cw-text-xs cw-mt-1">
              I can help you find the perfect property.<br />
              Tell me what you're looking for!
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        {loading && <TypingIndicator />}
      </div>

      {/* Input */}
      <ChatInput onSend={send} disabled={loading} />
    </div>
  );
}

/* ── Main Widget ──────────────────────────────────────────────── */

export default function Widget() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <ChatButton onClick={() => setIsOpen(true)} isOpen={isOpen} />
      {isOpen && <ChatWindow onClose={() => setIsOpen(false)} />}
    </>
  );
}
