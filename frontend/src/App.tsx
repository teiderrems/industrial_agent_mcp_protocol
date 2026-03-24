import { useState, useRef, useEffect } from "react";
import axios from "axios";
import SyntaxHighlighter from "react-syntax-highlighter";
import { vs2015 } from "react-syntax-highlighter/dist/esm/styles/hljs";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowUpOutlined,
  CloseOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  MenuOutlined,
  WarningFilled,
  ApartmentOutlined,
} from "@ant-design/icons";
import { Modal, Spin } from "antd";

interface Message {
  role: "user" | "assistant";
  content: string;
  sql_query?: string;
  results?: any;
  decision?: any;
  requires_human_intervention?: boolean;
  error?: boolean;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(
    null,
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [graphModalVisible, setGraphModalVisible] = useState(false);
  const [graphLoading, setGraphLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [graphImageUrl, setGraphImageUrl] = useState<string | null>(null);

  const quickSuggestions = [
    {
      text: "Quelle est la température moyenne des machines ?",
      category: "normal",
    },
    {
      text: "Quelle machine a la température la plus élevée ?",
      category: "warning",
    },
    {
      text: "Liste des machines avec une vibration > 8 mm/s",
      category: "warning",
    },
    { text: "Nombre d’événements de maintenance ce mois", category: "normal" },
    {
      text: "Quelles machines ont eu une maintenance récente ?",
      category: "normal",
    },
    {
      text: "Afficher les capteurs de la machine Presse A",
      category: "normal",
    },
    {
      text: "Quel est le temps d’arrêt moyen par machine ?",
      category: "warning",
    },
    { text: "Machines avec une température > 85°C", category: "critical" },
    { text: "Machines avec une pression > 10 bar", category: "critical" },
    {
      text: "Événements de maintenance de la dernière semaine",
      category: "normal",
    },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
    setStreamingMessage(null);
  };

  const streamText = (
    fullText: string,
    sql_query?: string,
    results?: any,
    decision?: any,
    requires_human_intervention?: boolean,
  ) => {
    let i = 0;
    const interval = setInterval(() => {
      if (i < fullText.length) {
        setStreamingMessage((prev) => ({
          role: "assistant",
          content: fullText.slice(0, i + 1),
          sql_query: i === fullText.length - 1 ? sql_query : undefined,
          results: i === fullText.length - 1 ? results : undefined,
          decision: i === fullText.length - 1 ? decision : undefined,
          requires_human_intervention:
            i === fullText.length - 1 ? requires_human_intervention : undefined,
        }));
        i++;
      } else {
        clearInterval(interval);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: fullText,
            sql_query,
            results,
            decision,
            requires_human_intervention,
          },
        ]);
        setStreamingMessage(null);
        setLoading(false);
      }
    }, 15);
    return interval;
  };

  const handleSend = async (question?: string) => {
    const textToSend = question !== undefined ? question : input;
    if (!textToSend.trim() || loading) return;

    const userMessage: Message = { role: "user", content: textToSend };
    setMessages((prev) => [...prev, userMessage]);
    if (question !== undefined) setInput("");
    else setInput("");
    setLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await axios.post(
        "http://localhost:8001/ask",
        { question: textToSend },
        { signal: controller.signal },
      );
      const data = response.data;
      if (data.error) throw new Error(data.error);
      const fullText = data.answer || "Réponse générée.";
      const sql = data.sql_query;
      const res = data.results;
      const decision = data.decision;
      const requires_human_intervention = data.requires_human_intervention;
      streamText(fullText, sql, res, decision, requires_human_intervention);
    } catch (error: any) {
      if (axios.isCancel(error)) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: " Requête annulée.", error: true },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              " Erreur : " +
              (error.response?.data?.error ||
                error.message ||
                "Impossible de contacter le serveur."),
            error: true,
          },
        ]);
      }
      setLoading(false);
    } finally {
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const fetchGraph = async () => {
    setGraphLoading(true);
    try {
      const response = await axios.get("/api/workflow/graph.png", {
        responseType: "blob",
      });
      const url = URL.createObjectURL(response.data);
      setGraphImageUrl(url);
      setGraphModalVisible(true);
    } catch (error) {
      console.error("Failed to fetch graph image", error);
    } finally {
      setGraphLoading(false);
    }
  };

  useEffect(() => {
    return () => {
      if (graphImageUrl) {
        URL.revokeObjectURL(graphImageUrl);
      }
    };
  }, [graphImageUrl]);

  const renderResults = (data: any) => {
    if (!data) return null;
    if (Array.isArray(data) && data.length > 0) {
      const columns = Object.keys(data[0]);
      return (
        <div className="overflow-x-auto mt-2">
          <table className="min-w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
            <thead className="bg-slate-50">
              <tr>
                {columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-2 text-left font-semibold text-slate-700"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((row: any, idx: number) => (
                <tr key={idx} className="hover:bg-slate-50">
                  {columns.map((col) => (
                    <td key={col} className="px-4 py-2 text-slate-600">
                      {row[col]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    } else if (typeof data === "object") {
      return (
        <pre className="bg-slate-100 p-2 rounded text-sm overflow-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
    } else {
      return <p className="text-slate-600">{String(data)}</p>;
    }
  };

  const DecisionCard = ({
    decision,
    requires_human_intervention,
  }: {
    decision: any;
    requires_human_intervention?: boolean;
  }) => {
    if (!decision || decision.status === "no_data") return null;

    const getStatusIcon = () => {
      switch (decision.status) {
        case "critical":
          return <WarningOutlined className="text-red-600 text-lg" />;
        case "warning":
          return (
            <ExclamationCircleOutlined className="text-amber-500 text-lg" />
          );
        default:
          return <CheckCircleOutlined className="text-green-600 text-lg" />;
      }
    };

    const getStatusColor = () => {
      switch (decision.status) {
        case "critical":
          return "border-red-500 bg-red-50";
        case "warning":
          return "border-amber-500 bg-amber-50";
        default:
          return "border-green-500 bg-green-50";
      }
    };

    const getStatusTextColor = () => {
      switch (decision.status) {
        case "critical":
          return "text-red-700";
        case "warning":
          return "text-amber-700";
        default:
          return "text-green-700";
      }
    };

    return (
      <div className={`mt-4 rounded-lg border-l-4 p-4 ${getStatusColor()}`}>
        <div className="flex items-center gap-2 mb-2">
          {getStatusIcon()}
          <span className={`font-semibold ${getStatusTextColor()}`}>
            {decision.status === "critical" && "Critique"}
            {decision.status === "warning" && "Alerte"}
            {decision.status === "normal" && "Normal"}
          </span>
        </div>
        <p className="text-sm text-slate-700">{decision.message}</p>
        {requires_human_intervention && (
          <div className="mt-2 text-xs font-medium text-red-600 flex items-center gap-1">
            <WarningOutlined /> Intervention humaine requise
          </div>
        )}
        {decision.details &&
          (decision.details.critical_count > 0 ||
            decision.details.warning_count > 0) && (
            <details className="mt-2">
              <summary className="text-xs cursor-pointer text-slate-500">
                Détails
              </summary>
              <ul className="text-xs text-slate-600 mt-1 ml-4 list-disc">
                {decision.details.critical_count > 0 && (
                  <li>⚠️ Critiques : {decision.details.critical_count}</li>
                )}
                {decision.details.warning_count > 0 && (
                  <li>⚠️ Alertes : {decision.details.warning_count}</li>
                )}
                {decision.details.critical_reasons?.length > 0 && (
                  <li>
                    Raisons critiques :{" "}
                    {decision.details.critical_reasons.join(", ")}
                  </li>
                )}
                {decision.details.warning_reasons?.length > 0 && (
                  <li>
                    Raisons d'alerte :{" "}
                    {decision.details.warning_reasons.join(", ")}
                  </li>
                )}
              </ul>
            </details>
          )}
      </div>
    );
  };

  return (
    <div className="bg-background text-on-background font-body antialiased flex h-screen">
      {/* Sidebar with suggestions as cards */}
      <div
        className={`
        fixed inset-y-0 left-0 transform ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        md:relative md:translate-x-0 transition-transform duration-300 ease-in-out z-30
        w-80 bg-white border-r border-slate-200 flex flex-col overflow-y-auto shadow-lg md:shadow-none
      `}
      >
        <div className="p-4 border-b border-slate-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold text-slate-900">Suggestions</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden text-slate-500 hover:text-slate-700"
          >
            <CloseOutlined />
          </button>
        </div>
        <div className="p-4 space-y-3">
          {quickSuggestions.map((sug, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(sug.text)}
              disabled={loading}
              className="w-full text-left p-3 rounded-xl bg-white border hover:cursor-pointer border-slate-200 hover:border-primary hover:shadow-md transition-all duration-200 disabled:opacity-50 group"
            >
              <p className="text-sm text-slate-700 group-hover:text-primary transition-colors">
                {sug.text}
              </p>
              {sug.category === "critical" && (
                <span className="inline-block mt-1 text-xs text-red-600 font-medium">
                  <WarningFilled /> Critique
                </span>
              )}
              {sug.category === "warning" && (
                <span className="inline-block mt-1 text-xs text-amber-600 font-medium">
                  <WarningFilled /> Alerte
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile toggle button */}
        <div className="md:hidden p-3 bg-white border-b border-slate-100 sticky top-0 z-20">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-slate-500 hover:text-slate-700"
          >
            <MenuOutlined />
          </button>
        </div>

        <header className="border-b border-slate-100 bg-white/70 backdrop-blur-xl sticky top-0 z-10 hidden md:block">
          <div className="max-w-3xl mx-auto px-4 py-3 flex justify-between items-center">
            <h1 className="text-xl font-bold text-slate-900">NL2SQL Agent</h1>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Azure Connected
            </div>
            <button
              onClick={fetchGraph}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              title="Voir le workflow LangGraph"
            >
              <ApartmentOutlined />
              Workflow
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.length === 0 && (
              <div className="text-center text-slate-400 mt-20">
                <p className="text-lg">
                  Posez une question sur vos données industrielles
                </p>
                <p className="text-sm mt-2">
                  Ex: "Quelle est la température moyenne de la machine Presse A
                  ?"
                </p>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-5 py-3 ${msg.role === "user" ? "bg-primary text-white rounded-br-none" : "bg-surface-container-low text-on-surface rounded-bl-none"}`}
                >
                  <div className="whitespace-pre-wrap break-words">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  {msg.role === "assistant" && msg.sql_query && (
                    <details className="mt-3">
                      <summary className="text-sm cursor-pointer text-primary font-medium">
                        🔍 Voir la requête SQL
                      </summary>
                      <div className="mt-2">
                        <SyntaxHighlighter
                          language="sql"
                          style={vs2015}
                          showLineNumbers
                          wrapLines={true}
                          lineProps={{
                            style: {
                              whiteSpace: "pre-wrap",
                              wordBreak: "break-word",
                            },
                          }}
                          customStyle={{
                            fontSize: "0.75rem",
                            margin: 0,
                            overflowX: "hidden",
                          }}
                        >
                          {msg.sql_query}
                        </SyntaxHighlighter>
                      </div>
                    </details>
                  )}
                  {msg.role === "assistant" && msg.results && (
                    <div className="mt-3">
                      <div className="text-sm font-medium text-on-surface-variant mb-1">
                        📊 Résultats
                      </div>
                      {renderResults(msg.results)}
                    </div>
                  )}
                  {msg.role === "assistant" && msg.decision && (
                    <DecisionCard
                      decision={msg.decision}
                      requires_human_intervention={
                        msg.requires_human_intervention
                      }
                    />
                  )}
                </div>
              </div>
            ))}
            {streamingMessage && (
              <div className="flex justify-start">
                <div className="bg-surface-container-low rounded-2xl rounded-bl-none px-5 py-3 max-w-[85%]">
                  <div className="whitespace-pre-wrap break-words">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {streamingMessage.content}
                    </ReactMarkdown>
                  </div>
                  {streamingMessage.sql_query && (
                    <details className="mt-3">
                      <summary className="text-sm cursor-pointer text-primary font-medium">
                        🔍 Voir la requête SQL
                      </summary>
                      <div className="mt-2">
                        <SyntaxHighlighter
                          language="sql"
                          style={vs2015}
                          showLineNumbers
                          wrapLines={true}
                          lineProps={{
                            style: {
                              whiteSpace: "pre-wrap",
                              wordBreak: "break-word",
                            },
                          }}
                          customStyle={{
                            fontSize: "0.75rem",
                            margin: 0,
                            overflowX: "hidden",
                          }}
                        >
                          {streamingMessage.sql_query}
                        </SyntaxHighlighter>
                      </div>
                    </details>
                  )}
                  {streamingMessage.results && (
                    <div className="mt-3">
                      <div className="text-sm font-medium text-on-surface-variant mb-1">
                        📊 Résultats
                      </div>
                      {renderResults(streamingMessage.results)}
                    </div>
                  )}
                  {streamingMessage.decision && (
                    <DecisionCard
                      decision={streamingMessage.decision}
                      requires_human_intervention={
                        streamingMessage.requires_human_intervention
                      }
                    />
                  )}
                </div>
              </div>
            )}
            {loading && !streamingMessage && (
              <div className="flex justify-start">
                <div className="bg-surface-container-low rounded-2xl rounded-bl-none px-5 py-3">
                  <div className="flex gap-1 items-center">
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="border-t border-slate-100 bg-white/80 backdrop-blur-sm sticky bottom-0">
          <div className="max-w-3xl mx-auto px-4 py-4">
            <div className="relative border border-slate-200 rounded-2xl bg-white shadow-sm focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
              <textarea
                ref={textareaRef}
                rows={1}
                className="w-full resize-y rounded-2xl px-4 py-3 focus:outline-none bg-transparent placeholder:text-slate-400"
                placeholder="Posez une question sur vos données industrielles. Ex: Quelle est la température moyenne de la machine Presse A ?"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                style={{ minHeight: "3rem" }}
              />
              <div className="flex items-center justify-end px-3 pb-3">
                <div className="flex items-center gap-2">
                  {loading ? (
                    <button
                      onClick={stopStreaming}
                      className="flex items-center justify-center hover:cursor-pointer w-8 h-8 rounded-full bg-blue-500 text-white transition"
                      title="Arrêter la génération"
                    >
                      <CloseOutlined />
                    </button>
                  ) : (
                    <button
                      onClick={() => handleSend()}
                      disabled={!input.trim()}
                      className="flex items-center justify-center bg-blue-500 w-8 h-8 rounded-full bg-primary text-white disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition"
                    >
                      <ArrowUpOutlined />
                    </button>
                  )}
                </div>
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-2 text-center">
              Appuyez sur Entrée pour envoyer
            </p>
          </div>
        </div>
      </div>

      {/* Modal for workflow graph */}
      <Modal
        title="Workflow LangGraph"
        open={graphModalVisible}
        onCancel={() => setGraphModalVisible(false)}
        footer={null}
        width="80%"
        style={{ top: 20 }}
        bodyStyle={{ maxHeight: "70vh", overflow: "auto", padding: "20px", display: "flex", justifyContent: "center", alignItems: "center" }}
      >
        {graphLoading ? (
          <div className="flex justify-center py-12">
            <Spin size="large" />
          </div>
        ) : (
          graphImageUrl && (
            <img
              src={graphImageUrl}
              alt="LangGraph workflow"
              style={{ width: "400px", height: "fit-content" }}
            />
          )
        )}
      </Modal>
    </div>
  );
}

export default App;
