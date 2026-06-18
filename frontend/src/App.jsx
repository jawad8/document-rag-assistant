import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [docsOpen, setDocsOpen] = useState(false);
  const [documents, setDocuments] = useState([]);

  async function login(event) {
    event.preventDefault();
    setError("");

    const response = await fetch(`${API_BASE_URL}/api/token/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      setError("Sign-in failed. Check your username and password.");
      return;
    }

    const data = await response.json();
    localStorage.setItem("token", data.access);
    setToken(data.access);
  }

  function logout() {
    localStorage.removeItem("token");
    setToken(null);
    setDocuments([]);
    setMessages([]);
  }

  async function fetchDocs() {
    if (!token) return;

    const response = await fetch(`${API_BASE_URL}/documents/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 401) {
      logout();
      return;
    }

    if (response.ok) {
      setDocuments(await response.json());
    }
  }

  async function uploadFile(file) {
    if (!file) return;

    const form = new FormData();
    form.append("title", file.name);
    form.append("file", file);

    const response = await fetch(`${API_BASE_URL}/documents/upload/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });

    if (!response.ok) {
      setError("The document could not be uploaded.");
      return;
    }

    fetchDocs();
  }

  async function deleteDoc(id) {
    await fetch(`${API_BASE_URL}/documents/${id}/`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    fetchDocs();
  }

  async function send() {
    if (!input.trim() || loading) return;

    const question = input;
    setMessages((current) => [...current, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/chat/ask/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok || !response.body) {
        throw new Error("The assistant could not answer that question.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let answer = "";
      let sources = [];
      let firstChunk = true;

      setMessages((current) => [
        ...current,
        { role: "assistant", text: "", sources: [] },
      ]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        if (firstChunk) {
          const lines = chunk.split("\n");
          sources = JSON.parse(lines[0]).sources;
          answer += lines.slice(1).join("");
          firstChunk = false;
        } else {
          answer += chunk;
        }

        // Streaming intentionally updates the final message for each chunk.
        // eslint-disable-next-line no-loop-func
        setMessages((current) => {
          const next = [...current];
          next[next.length - 1] = {
            role: "assistant",
            text: answer,
            sources,
          };
          return next;
        });
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDocs();
    // fetchDocs is scoped to the active token and should run when it changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (!token) {
    return (
      <main className="min-h-screen grid place-items-center px-6 text-white">
        <form
          onSubmit={login}
          className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-950/75 p-8 shadow-2xl backdrop-blur"
        >
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">
            Grounded answers
          </p>
          <h1 className="mt-3 text-4xl font-bold">Document RAG Assistant</h1>
          <p className="mt-3 text-slate-400">
            Sign in to search your private document workspace.
          </p>

          <div className="mt-8 space-y-4">
            <input
              required
              value={credentials.username}
              onChange={(event) =>
                setCredentials({ ...credentials, username: event.target.value })
              }
              placeholder="Username"
              className="w-full rounded-xl border border-white/10 bg-white/5 p-3 outline-none focus:border-cyan-400"
            />
            <input
              required
              type="password"
              value={credentials.password}
              onChange={(event) =>
                setCredentials({ ...credentials, password: event.target.value })
              }
              placeholder="Password"
              className="w-full rounded-xl border border-white/10 bg-white/5 p-3 outline-none focus:border-cyan-400"
            />
          </div>

          {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}

          <button className="mt-6 w-full rounded-xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-3 font-semibold text-slate-950">
            Sign in
          </button>
        </form>
      </main>
    );
  }

  return (
    <div className="flex min-h-screen flex-col text-white">
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/75 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <button onClick={() => setDocsOpen(!docsOpen)} className="text-left">
            <span className="block text-xs uppercase tracking-[0.25em] text-cyan-300">
              Knowledge workspace
            </span>
            <span className="text-2xl font-bold">Document RAG Assistant</span>
          </button>
          <button
            onClick={logout}
            className="rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300 hover:bg-white/5"
          >
            Sign out
          </button>
        </div>

        <AnimatePresence>
          {docsOpen && (
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: "auto" }}
              exit={{ height: 0 }}
              className="overflow-hidden border-t border-white/10"
            >
              <div className="mx-auto max-w-5xl space-y-2 px-6 py-4">
                {documents.map((document) => (
                  <div
                    key={document.id}
                    className="flex items-center justify-between rounded-xl bg-white/5 p-3 text-sm"
                  >
                    <span>{document.title}</span>
                    <button
                      onClick={() => deleteDoc(document.id)}
                      className="text-rose-300 hover:text-rose-200"
                    >
                      Delete
                    </button>
                  </div>
                ))}
                {!documents.length && (
                  <p className="text-sm text-slate-400">No documents uploaded.</p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-8">
        <div className="flex-1 space-y-4">
          {!messages.length && (
            <div className="rounded-3xl border border-white/10 bg-white/5 p-8">
              <p className="text-sm uppercase tracking-[0.2em] text-violet-300">
                Ready when you are
              </p>
              <h2 className="mt-2 text-3xl font-semibold">
                Ask questions grounded in your documents.
              </h2>
              <p className="mt-3 max-w-2xl text-slate-400">
                Upload a UTF-8 text file, then ask for summaries, comparisons,
                evidence, or answers with source attribution.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <motion.div
              key={index}
              className={`max-w-2xl rounded-2xl p-4 ${
                message.role === "user"
                  ? "ml-auto bg-cyan-400/15"
                  : "bg-violet-400/15"
              }`}
            >
              {message.text}
              {!!message.sources?.length && (
                <div className="mt-3 border-t border-white/10 pt-3 text-xs text-cyan-200">
                  Sources: {message.sources.join(", ")}
                </div>
              )}
            </motion.div>
          ))}

          {loading && <p className="animate-pulse text-slate-400">Thinking…</p>}
          {error && <p className="text-sm text-rose-300">{error}</p>}
        </div>

        <div className="sticky bottom-0 mt-8 flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/85 p-3 backdrop-blur">
          <label className="cursor-pointer rounded-xl border border-white/10 px-4 py-3 text-sm hover:bg-white/5">
            Upload
            <input
              type="file"
              accept=".txt,text/plain"
              hidden
              onChange={(event) => uploadFile(event.target.files?.[0])}
            />
          </label>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") send();
            }}
            placeholder="Ask a question or paste a URL…"
            className="flex-1 bg-transparent p-3 outline-none"
          />
          <button
            onClick={send}
            disabled={loading}
            className="rounded-xl bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </main>
    </div>
  );
}
