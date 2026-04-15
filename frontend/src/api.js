const BASE = import.meta.env.VITE_API_URL || "http://localhost:8080";

export const api = {
  health: () =>
    fetch(`${BASE}/health`).then(r => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }),

  stats: (key) =>
    fetch(`${BASE}/stats`, {
      headers: { "X-API-Key": key },
    }).then(r => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }),

  chat: (key, query, conversationId = null) =>
    fetch(`${BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": key,
      },
      body: JSON.stringify({
        query,
        ...(conversationId && { conversation_id: conversationId }),
      }),
    }).then(r => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }),

  getConversation: (key, id) =>
    fetch(`${BASE}/conversations/${encodeURIComponent(id)}`, {
      headers: { "X-API-Key": key },
    }).then(r => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }),

  deleteConversation: (key, id) =>
    fetch(`${BASE}/conversations/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: { "X-API-Key": key },
    }).then(r => {
      if (!r.ok) throw new Error(r.status);
      if (r.status === 204) return null;
      return r.text().then(text => text ? JSON.parse(text) : null);
    }),
};
