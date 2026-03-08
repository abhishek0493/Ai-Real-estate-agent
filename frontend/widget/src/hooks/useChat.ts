import { useState, useCallback, useEffect } from "react";
import { sendMessage, ChatResponse } from "../services/chatApi";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const LEAD_KEY = "chat_lead_id";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [leadId, setLeadId] = useState<string | undefined>(() => {
    try {
      return localStorage.getItem(LEAD_KEY) || undefined;
    } catch {
      return undefined;
    }
  });

  // Persist leadId
  useEffect(() => {
    try {
      if (leadId) localStorage.setItem(LEAD_KEY, leadId);
    } catch {}
  }, [leadId]);

  const send = useCallback(
    async (text: string) => {
      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      try {
        const data: ChatResponse = await sendMessage(text, leadId);

        // Save lead_id from first response
        if (data.lead_id && data.lead_id !== leadId) {
          setLeadId(data.lead_id);
        }

        const assistantMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.assistant_message,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch {
        const errorMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Something went wrong. Please try again.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [leadId]
  );

  const reset = useCallback(() => {
    setMessages([]);
    setLeadId(undefined);
    try {
      localStorage.removeItem(LEAD_KEY);
    } catch {}
  }, []);

  return { messages, loading, leadId, send, reset };
}
