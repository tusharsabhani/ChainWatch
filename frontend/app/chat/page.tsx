import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { ErrorState } from "@/components/states/error-state";
import { getChatMessages, getChatSessions } from "@/lib/api";
import { safeApiCall } from "@/lib/api/client";

type SearchParams = Record<string, string | string[] | undefined>;

function readSearchParam(searchParams: SearchParams, key: string) {
  const value = searchParams[key];
  return Array.isArray(value) ? value[0] : value;
}

export default async function ChatPage({
  searchParams
}: {
  searchParams: SearchParams;
}) {
  const contextScope = readSearchParam(searchParams, "contextScope") || "global";
  const contextId = readSearchParam(searchParams, "contextId") || null;
  const selectedSessionFromQuery = readSearchParam(searchParams, "sessionId") || null;

  const sessionsResult = await safeApiCall(() => getChatSessions());
  const sessions = sessionsResult.data?.items ?? [];
  const hasContextSeed = contextScope !== "global" || Boolean(contextId);
  const matchingContextSession = hasContextSeed
    ? sessions.find(
        (session) =>
          session.contextScope === contextScope &&
          (contextId ? session.contextId === contextId : true)
      ) ?? null
    : null;
  const selectedSessionId =
    selectedSessionFromQuery || matchingContextSession?.id || sessions[0]?.id || null;
  const conversationResult = selectedSessionId
    ? await safeApiCall(() => getChatMessages(selectedSessionId))
    : { data: null, error: null };

  if (sessionsResult.error && !sessionsResult.data) {
    return (
      <div className="p-4 lg:p-8">
        <ErrorState
          title="Chat workspace unavailable"
          message={sessionsResult.error.message}
        />
      </div>
    );
  }

  return (
    <ChatWorkspace
      initialSessions={sessions}
      initialConversation={conversationResult.data}
      initialContextScope={contextScope}
      initialContextId={contextId}
    />
  );
}
