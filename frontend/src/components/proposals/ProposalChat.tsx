"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

interface ProposalChatProps {
  proposalId: string;
  proposalTitle: string;
}

export function ProposalChat({ proposalId, proposalTitle }: ProposalChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load conversation history when opened
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      loadHistory();
    }
  }, [isOpen]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const response = await api.proposals.getChatHistory(proposalId);
      setMessages(response.conversation_history);
    } catch (err) {
      // No history yet, that's fine
      console.log("No chat history yet");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setError(null);
    setIsLoading(true);

    // Optimistically add user message
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const response = await api.proposals.chat(proposalId, userMessage);
      setMessages(response.conversation_history);
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
      // Remove optimistic message on error
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const suggestedQuestions = [
    "この提案のリスクは何ですか？",
    "他の方法はありますか？",
    "期待効果の根拠を教えてください",
    "実行前に確認すべきことは？",
  ];

  return (
    <div className="border-t border-gray-200 mt-4 pt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-4 w-4 transform transition-transform ${isOpen ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        AIに相談する（壁打ち）
      </button>

      {isOpen && (
        <div className="mt-4 border border-gray-200 rounded-lg bg-gray-50">
          {/* Chat messages area */}
          <div className="h-64 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && !isLoading && (
              <div className="text-center text-gray-500 text-sm py-8">
                <p className="mb-4">この提案について質問や相談ができます</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(q)}
                      className="text-xs bg-white border border-gray-300 rounded-full px-3 py-1 hover:bg-blue-50 hover:border-blue-300"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white border border-gray-200 text-gray-800"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg px-4 py-2">
                  <div className="flex items-center gap-2 text-gray-500">
                    <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-blue-600 rounded-full"></div>
                    <span className="text-sm">考え中...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Error message */}
          {error && (
            <div className="px-4 py-2 bg-red-50 text-red-700 text-sm border-t border-red-200">
              {error}
            </div>
          )}

          {/* Input area */}
          <form onSubmit={handleSubmit} className="border-t border-gray-200 p-3 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="質問を入力..."
              disabled={isLoading}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              送信
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
