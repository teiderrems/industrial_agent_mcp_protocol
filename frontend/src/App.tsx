import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowUpOutlined, CloseOutlined } from '@ant-design/icons';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sql_query?: string;
  results?: any;
  error?: boolean;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);
  const [deepThink, setDeepThink] = useState(false);
  const [search, setSearch] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
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

  const streamText = (fullText: string, sql_query?: string, results?: any) => {
    let i = 0;
    const interval = setInterval(() => {
      if (i < fullText.length) {
        setStreamingMessage((prev) => ({
          role: 'assistant',
          content: fullText.slice(0, i + 1),
          sql_query: i === fullText.length - 1 ? sql_query : undefined,
          results: i === fullText.length - 1 ? results : undefined,
        }));
        i++;
      } else {
        clearInterval(interval);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: fullText,
            sql_query,
            results,
          },
        ]);
        setStreamingMessage(null);
        setLoading(false);
      }
    }, 15);
    return interval;
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await axios.post(
        'http://localhost:8001/ask',
        { question: input },
        { signal: controller.signal }
      );
      const data = response.data;
      if (data.error) throw new Error(data.error);
      const fullText = data.answer || 'Réponse générée.';
      const sql = data.sql_query;
      const res = data.results;
      streamText(fullText, sql, res);
    } catch (error: any) {
      if (axios.isCancel(error)) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '❌ Requête annulée.', error: true },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: '❌ Erreur : ' + (error.response?.data?.error || error.message || 'Impossible de contacter le serveur.'),
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
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

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
                  <th key={col} className="px-4 py-2 text-left font-semibold text-slate-700">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((row: any, idx: number) => (
                <tr key={idx} className="hover:bg-slate-50">
                  {columns.map((col) => (
                    <td key={col} className="px-4 py-2 text-slate-600">{row[col]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    } else if (typeof data === 'object') {
      return <pre className="bg-slate-100 p-2 rounded text-sm overflow-auto">{JSON.stringify(data, null, 2)}</pre>;
    } else {
      return <p className="text-slate-600">{String(data)}</p>;
    }
  };

  const quickSuggestions = [
    'Quelle est la température moyenne des machines ?',
    'Liste des machines avec le plus de temps d’arrêt',
    'Nombre d’événements de maintenance ce mois',
  ];

  return (
    <div className="bg-background text-on-background font-body antialiased flex flex-col h-screen">
      <header className="border-b border-slate-100 bg-white/70 backdrop-blur-xl sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3 flex justify-between items-center">
          <h1 className="text-xl font-bold text-slate-900">NL2SQL Agent</h1>
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            Azure Connected
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="text-center text-slate-400 mt-20">
              <p className="text-lg">Posez une question sur vos données industrielles</p>
              <p className="text-sm mt-2">Ex: "Quelle est la température moyenne de la machine Presse A ?"</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl px-5 py-3 ${msg.role === 'user' ? 'bg-primary text-white rounded-br-none' : 'bg-surface-container-low text-on-surface rounded-bl-none'}`}>
                <div className="whitespace-pre-wrap break-words">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
                {msg.role === 'assistant' && msg.sql_query && (
                  <details className="mt-3">
                    <summary className="text-sm cursor-pointer text-primary font-medium">🔍 Voir la requête SQL</summary>
                    <SyntaxHighlighter language="sql" style={vs2015} showLineNumbers customStyle={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>
                      {msg.sql_query}
                    </SyntaxHighlighter>
                  </details>
                )}
                {msg.role === 'assistant' && msg.results && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-on-surface-variant mb-1">📊 Résultats</div>
                    {renderResults(msg.results)}
                  </div>
                )}
              </div>
            </div>
          ))}
          {streamingMessage && (
            <div className="flex justify-start">
              <div className="bg-surface-container-low rounded-2xl rounded-bl-none px-5 py-3 max-w-[85%]">
                <div className="whitespace-pre-wrap break-words">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingMessage.content}</ReactMarkdown>
                </div>
                {streamingMessage.sql_query && (
                  <details className="mt-3">
                    <summary className="text-sm cursor-pointer text-primary font-medium">🔍 Voir la requête SQL</summary>
                    <SyntaxHighlighter language="sql" style={vs2015} showLineNumbers customStyle={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>
                      {streamingMessage.sql_query}
                    </SyntaxHighlighter>
                  </details>
                )}
                {streamingMessage.results && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-on-surface-variant mb-1">📊 Résultats</div>
                    {renderResults(streamingMessage.results)}
                  </div>
                )}
              </div>
            </div>
          )}
          {loading && !streamingMessage && (
            <div className="flex justify-start">
              <div className="bg-surface-container-low rounded-2xl rounded-bl-none px-5 py-3">
                <div className="flex gap-1 items-center">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-slate-100 bg-white/80 backdrop-blur-sm sticky bottom-0">
        <div className="max-w-3xl mx-auto px-4 py-4">
          {messages.length === 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {quickSuggestions.map((sug, i) => (
                <button key={i} onClick={() => setInput(sug)} className="text-xs hover:cursor-pointer bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-full transition">
                  {sug}
                </button>
              ))}
            </div>
          )}
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
              style={{ minHeight: '3rem' }}
            />
            <div className="flex items-center justify-end px-3 pb-3">
              <div className="flex items-center gap-2">
                {loading ? (
                  <button
                    onClick={stopStreaming}
                    className="flex items-center justify-center hover:cursor-pointer w-8 h-8 rounded-full bg-blue-500 text-white  transition"
                    title="Arrêter la génération"
                  >
                    <CloseOutlined />
                  </button>
                ) : (
                  <button
                    onClick={handleSend}
                    disabled={!input.trim()}
                    className="flex items-center justify-center bg-blue-500 w-8 h-8 rounded-full bg-primary text-white disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition"
                  >
                    <ArrowUpOutlined />
                  </button>
                )}
              </div>
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-2 text-center">Appuyez sur Entrée pour envoyer</p>
        </div>
      </div>
    </div>
  );
}

export default App;