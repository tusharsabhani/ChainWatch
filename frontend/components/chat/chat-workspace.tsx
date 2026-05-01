"use client";

import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { MaterialIcon } from "@/components/material-icon";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import type {
  ChatCreateSessionResponse,
  ChatMessagesResponse,
  ChatPostMessageResponse,
  ChatSessionsResponse
} from "@/lib/api/types";
import { localApiRequest, safeLocalApiCall } from "@/lib/local-api";
import { cx, formatDateTime } from "@/lib/utils";

type SessionItem = ChatSessionsResponse["items"][number];
type MessageItem = ChatMessagesResponse["messages"][number];

const CONTEXT_OPTIONS = [
  { label: "Global", value: "global" },
  { label: "Product", value: "product" },
  { label: "Country", value: "country" },
  { label: "Supplier", value: "supplier" }
] as const;

function buildTitle(contextScope: string, contextId: string, seedMessage?: string) {
  if (contextScope !== "global" && contextId) {
    return `${contextScope}: ${contextId}`;
  }

  if (seedMessage) {
    return seedMessage.slice(0, 48);
  }

  return "New Chat";
}

function makeConversationMap(initialConversation: ChatMessagesResponse | null) {
  if (!initialConversation) {
    return {} as Record<string, ChatMessagesResponse>;
  }

  return {
    [initialConversation.session.id]: initialConversation
  };
}

export function ChatWorkspace({
  initialSessions,
  initialConversation,
  initialContextScope,
  initialContextId
}: {
  initialSessions: SessionItem[];
  initialConversation: ChatMessagesResponse | null;
  initialContextScope: string;
  initialContextId: string | null;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [sessions, setSessions] = useState<SessionItem[]>(initialSessions);
  const [conversations, setConversations] = useState<Record<string, ChatMessagesResponse>>(
    makeConversationMap(initialConversation)
  );
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    initialConversation?.session.id ?? initialSessions[0]?.id ?? null
  );
  const [composer, setComposer] = useState("");
  const [contextScope, setContextScope] = useState(initialContextScope);
  const [contextId, setContextId] = useState(initialContextId ?? "");
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [banner, setBanner] = useState<{
    tone: "success" | "caution" | "danger";
    message: string;
  } | null>(null);

  const selectedConversation = selectedSessionId
    ? conversations[selectedSessionId] ?? null
    : null;
  const latestAssistantMessage = useMemo(() => {
    const messages = selectedConversation?.messages ?? [];
    return [...messages].reverse().find((message) => message.role === "assistant") ?? null;
  }, [selectedConversation]);

  function updateUrl(
    nextSessionId: string | null,
    nextContextScope = contextScope,
    nextContextId = contextId
  ) {
    const nextParams = new URLSearchParams(searchParams.toString());

    if (nextSessionId) {
      nextParams.set("sessionId", nextSessionId);
    } else {
      nextParams.delete("sessionId");
    }

    if (nextContextScope && nextContextScope !== "global") {
      nextParams.set("contextScope", nextContextScope);
    } else {
      nextParams.delete("contextScope");
    }

    if (nextContextId.trim()) {
      nextParams.set("contextId", nextContextId.trim());
    } else {
      nextParams.delete("contextId");
    }

    const queryString = nextParams.toString();
    router.replace(queryString ? `/chat?${queryString}` : "/chat", { scroll: false });
  }

  async function loadConversation(sessionId: string) {
    setLoadingSessionId(sessionId);
    setBanner(null);
    const result = await safeLocalApiCall(() =>
      localApiRequest<ChatMessagesResponse>(`chat/sessions/${sessionId}/messages`)
    );
    setLoadingSessionId(null);

    if (!result.data) {
      setBanner({
        tone: "danger",
        message: result.error?.message || "The conversation could not be loaded."
      });
      return;
    }

    setConversations((current) => ({
      ...current,
      [sessionId]: result.data as ChatMessagesResponse
    }));
  }

  async function ensureSession(seedMessage?: string) {
    if (selectedSessionId) {
      return selectedSessionId;
    }

    setIsCreating(true);
    setBanner(null);
    const result = await safeLocalApiCall(() =>
      localApiRequest<ChatCreateSessionResponse>("chat/sessions", {
        method: "POST",
        body: {
          title: buildTitle(contextScope, contextId.trim(), seedMessage),
          contextScope,
          contextId: contextScope === "global" ? null : contextId.trim() || null
        }
      })
    );
    setIsCreating(false);

    if (!result.data) {
      setBanner({
        tone: "danger",
        message: result.error?.message || "A new chat session could not be created."
      });
      return null;
    }

    const newSession: SessionItem = {
      id: result.data.id,
      title: result.data.title,
      contextScope: result.data.contextScope,
      contextId: result.data.contextId,
      updatedAt: result.data.createdAt
    };

    setSessions((current) => [newSession, ...current.filter((item) => item.id !== newSession.id)]);
    setConversations((current) => ({
      ...current,
      [newSession.id]: {
        session: {
          id: newSession.id,
          title: newSession.title
        },
        messages: []
      }
    }));
    setSelectedSessionId(newSession.id);
    updateUrl(newSession.id);
    return newSession.id;
  }

  async function handleSelectSession(sessionId: string) {
    setSelectedSessionId(sessionId);
    updateUrl(sessionId);
    if (!conversations[sessionId]) {
      await loadConversation(sessionId);
    }
  }

  async function handleCreateSession() {
    const sessionId = await ensureSession();
    if (sessionId && !conversations[sessionId]) {
      await loadConversation(sessionId);
    }
  }

  async function handleSendMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const message = composer.trim();
    if (!message || isSending) {
      return;
    }

    let sessionId = selectedSessionId;
    if (!sessionId) {
      sessionId = await ensureSession(message);
    }

    if (!sessionId) {
      return;
    }

    setIsSending(true);
    setBanner(null);
    const result = await safeLocalApiCall(() =>
      localApiRequest<ChatPostMessageResponse>("chat/messages", {
        method: "POST",
        body: {
          sessionId,
          message
        }
      })
    );
    setIsSending(false);

    if (!result.data) {
      setBanner({
        tone: "danger",
        message: result.error?.message || "The message could not be sent."
      });
      return;
    }

    const payload = result.data;
    setComposer("");
    setConversations((current) => {
      const existing = current[sessionId!] ?? {
        session: {
          id: sessionId!,
          title: sessions.find((item) => item.id === sessionId)?.title || "New Chat"
        },
        messages: []
      };

      return {
        ...current,
        [sessionId!]: {
          ...existing,
          messages: [
            ...existing.messages,
            payload.userMessage,
            payload.assistantMessage
          ]
        }
      };
    });
    setSessions((current) => {
      const target = current.find((item) => item.id === sessionId);
      const updatedSession: SessionItem = {
        id: sessionId!,
        title: target?.title || buildTitle(contextScope, contextId.trim(), message),
        contextScope: target?.contextScope || contextScope,
        contextId: target?.contextId ?? (contextScope === "global" ? null : contextId.trim() || null),
        updatedAt: payload.assistantMessage.createdAt
      };

      return [
        updatedSession,
        ...current.filter((item) => item.id !== sessionId)
      ];
    });
  }

  return (
    <div className="min-h-screen bg-background lg:h-[calc(100vh-64px)] lg:overflow-hidden">
      <div className="grid min-h-full lg:grid-cols-[300px,minmax(0,1fr),340px]">
        <aside className="border-b border-slate-200 bg-white lg:border-b-0 lg:border-r">
          <div className="space-y-5 p-4 lg:p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Chat Sessions
                </p>
                <h1 className="mt-2 font-display text-[22px] font-semibold tracking-[-0.02em] text-slate-950">
                  Intelligence Assistant
                </h1>
              </div>
              <button
                type="button"
                onClick={handleCreateSession}
                disabled={isCreating}
                className="inline-flex items-center gap-2 rounded-lg bg-secondary px-3 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white disabled:opacity-60"
              >
                <MaterialIcon icon="add" className="text-[16px]" />
                {isCreating ? "Creating" : "New"}
              </button>
            </div>

            <SectionCard title="Context" eyebrow="Optional scope">
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {CONTEXT_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => {
                        const nextContextScope = option.value;
                        const nextContextId = option.value === "global" ? "" : contextId;
                        setContextScope(option.value);
                        if (option.value === "global") {
                          setContextId("");
                        }
                        updateUrl(selectedSessionId, nextContextScope, nextContextId);
                      }}
                      className={cx(
                        "rounded-full px-3 py-1.5 font-label text-[10px] font-semibold uppercase tracking-[0.16em]",
                        contextScope === option.value
                          ? "bg-secondary text-white"
                          : "border border-outline-variant bg-white text-slate-600"
                      )}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
                <input
                  value={contextId}
                  onChange={(event) => setContextId(event.target.value)}
                  onBlur={() => updateUrl(selectedSessionId)}
                  placeholder={contextScope === "global" ? "No context needed" : "Scope id, e.g. 1 or VN"}
                  disabled={contextScope === "global"}
                  className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 disabled:bg-slate-100"
                />
              </div>
            </SectionCard>

            <div className="space-y-2">
              {sessions.length > 0 ? (
                sessions.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    onClick={() => handleSelectSession(session.id)}
                    className={cx(
                      "w-full rounded-lg border p-4 text-left transition",
                      selectedSessionId === session.id
                        ? "border-secondary bg-surface-container-low"
                        : "border-outline-variant bg-white hover:border-secondary/40"
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-data text-sm text-slate-950">{session.title}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {session.contextScope}
                          {session.contextId ? ` • ${session.contextId}` : ""}
                        </p>
                      </div>
                      {loadingSessionId === session.id ? (
                        <span className="text-xs text-slate-400">Loading</span>
                      ) : null}
                    </div>
                    <p className="mt-3 text-xs text-slate-500">
                      Updated {formatDateTime(session.updatedAt)}
                    </p>
                  </button>
                ))
              ) : (
                <EmptyState
                  title="No chat sessions yet"
                  description="Create a session to start asking questions about products, countries, suppliers, and risk events."
                />
              )}
            </div>
          </div>
        </aside>

        <section className="flex min-h-[480px] flex-col border-b border-slate-200 bg-background lg:border-b-0 lg:border-r">
          <div className="flex-1 space-y-6 overflow-y-auto p-4 lg:p-6">
            {banner ? (
              <div
                className={cx(
                  "rounded-lg border px-4 py-3 text-sm",
                  banner.tone === "success"
                    ? "border-secondary/20 bg-secondary/10 text-secondary"
                    : banner.tone === "caution"
                      ? "border-caution/20 bg-caution/10 text-caution"
                      : "border-error/20 bg-error/10 text-error"
                )}
              >
                {banner.message}
              </div>
            ) : null}

            {selectedConversation ? (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-display text-[22px] font-semibold tracking-[-0.02em] text-slate-950">
                      {selectedConversation.session.title}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      Context {contextScope}
                      {contextId ? ` • ${contextId}` : ""}
                    </p>
                  </div>
                  <StatusPill tone="success">Live</StatusPill>
                </div>

                {selectedConversation.messages.length > 0 ? (
                  <div className="space-y-5">
                    {selectedConversation.messages.map((message) => (
                      <div
                        key={message.id}
                        className={cx(
                          "flex gap-3",
                          message.role === "user" ? "justify-end" : "justify-start"
                        )}
                      >
                        {message.role !== "user" ? (
                          <div className="mt-1 flex h-9 w-9 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
                            <MaterialIcon icon="smart_toy" className="text-[18px]" />
                          </div>
                        ) : null}

                        <div className={cx("max-w-3xl", message.role === "user" && "text-right")}>
                          <div
                            className={cx(
                              "rounded-xl border p-4 shadow-overlay",
                              message.role === "user"
                                ? "rounded-tr-none border-primary-container bg-primary-container text-white"
                                : "rounded-tl-none border-outline-variant bg-white text-slate-800"
                            )}
                          >
                            <p className="whitespace-pre-wrap text-sm leading-7">
                              {message.messageText}
                            </p>

                            {message.citations?.length ? (
                              <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
                                {message.citations.map((citation) => (
                                  <a
                                    key={`${message.id}-${citation.url}`}
                                    href={citation.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] text-secondary"
                                  >
                                    <MaterialIcon icon="link" className="text-[14px]" />
                                    {citation.sourceName}
                                  </a>
                                ))}
                              </div>
                            ) : null}

                            {message.limitations?.length ? (
                              <div className="mt-4 space-y-2 border-t border-slate-100 pt-4">
                                {message.limitations.map((limitation) => (
                                  <p key={limitation} className="text-xs text-slate-500">
                                    Limitation: {limitation}
                                  </p>
                                ))}
                              </div>
                            ) : null}
                          </div>

                          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                            <span>{formatDateTime(message.createdAt)}</span>
                            {message.usedAgents?.length ? (
                              <>
                                <span>•</span>
                                <span>Agents: {message.usedAgents.join(", ")}</span>
                              </>
                            ) : null}
                          </div>
                        </div>

                        {message.role === "user" ? (
                          <div className="mt-1 flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-slate-600">
                            <MaterialIcon icon="person" className="text-[18px]" />
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="No messages yet"
                    description="Send the first question in this session to ask about risk, inventory, fulfillment, or reports."
                  />
                )}
              </>
            ) : (
              <EmptyState
                title="Choose or create a session"
                description="Use the sidebar to open a saved chat or start a new one with optional product, country, or supplier context."
              />
            )}
          </div>

          <div className="border-t border-slate-200 bg-white/85 p-4 backdrop-blur">
            <form onSubmit={handleSendMessage} className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {contextScope !== "global" ? (
                  <StatusPill tone="caution">
                    {contextScope}
                    {contextId ? `:${contextId}` : ""}
                  </StatusPill>
                ) : (
                  <StatusPill tone="neutral">global</StatusPill>
                )}
                <StatusPill tone="success">
                  {selectedSessionId ? "existing session" : "new session on send"}
                </StatusPill>
              </div>
              <div className="rounded-xl border border-outline-variant bg-white p-4 shadow-overlay">
                <textarea
                  rows={3}
                  value={composer}
                  onChange={(event) => setComposer(event.target.value)}
                  placeholder="Ask about product risk, country exposure, fulfillment delays, or next actions..."
                  className="w-full resize-none border-none bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
                />
                <div className="mt-4 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <MaterialIcon icon="shield" className="text-[16px]" />
                    Structured responses with citations when available
                  </div>
                  <button
                    type="submit"
                    disabled={isSending || !composer.trim()}
                    className="inline-flex items-center gap-2 rounded bg-secondary px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white disabled:opacity-60"
                  >
                    {isSending ? "Analyzing" : "Send"}
                    <MaterialIcon icon="send" className="text-[16px]" />
                  </button>
                </div>
              </div>
            </form>
          </div>
        </section>

        <aside className="border-t border-slate-200 bg-white lg:border-t-0">
          <div className="space-y-5 p-4 lg:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Intelligence Stack
                </p>
                <h2 className="mt-2 font-display text-[20px] font-semibold tracking-[-0.02em] text-slate-950">
                  Latest Response Context
                </h2>
              </div>
              <StatusPill tone="success">Ready</StatusPill>
            </div>

            {latestAssistantMessage ? (
              <div className="space-y-4">
                <SectionCard title="Used Agents" eyebrow="Deterministic routing">
                  {latestAssistantMessage.usedAgents?.length ? (
                    <div className="flex flex-wrap gap-2">
                      {latestAssistantMessage.usedAgents.map((agent) => (
                        <StatusPill key={agent} tone="neutral">
                          {agent}
                        </StatusPill>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-600">No agent metadata was returned for the selected response.</p>
                  )}
                </SectionCard>

                <SectionCard title="Citations" eyebrow="Grounding sources">
                  {latestAssistantMessage.citations?.length ? (
                    <div className="space-y-3">
                      {latestAssistantMessage.citations.map((citation) => (
                        <a
                          key={`${citation.url}-${citation.title}`}
                          href={citation.url}
                          target="_blank"
                          rel="noreferrer"
                          className="block rounded-lg border border-outline-variant bg-surface-container-low p-4 transition hover:border-secondary"
                        >
                          <p className="font-data text-sm text-slate-950">{citation.title}</p>
                          <p className="mt-1 text-xs text-slate-500">{citation.sourceName}</p>
                          {citation.snippet ? (
                            <p className="mt-2 text-sm leading-6 text-slate-600">{citation.snippet}</p>
                          ) : null}
                        </a>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      title="No citations returned"
                      description="This response did not rely on any external citations, which usually means the answer was assembled from local deterministic signals."
                    />
                  )}
                </SectionCard>
              </div>
            ) : (
              <EmptyState
                title="No assistant output yet"
                description="Once a response arrives, the latest used-agent summary and citation list will appear here."
              />
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
