import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { PanelLeft, Plus, ExternalLink, User, Send, X, MessageSquare, ChevronDown, MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
import DocsOverlay from './components/DocsOverlay';

const API_BASE = "http://localhost:8000/api";
const DUMMY_APIS = [
  { platform: 'Github', rename: 'Frontend Repo' },
  { platform: 'Notion', rename: 'Team Docs' },
  { platform: 'Discord', rename: 'Support Server' },
];

export default function App() {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [links, setLinks] = useState([]);
  const [conversations, setConversations] = useState([
    { id: 1, title: "New Conversation" }
  ]);
  const [activeConversationId, setActiveConversationId] = useState(1);
  const [openConversationMenuId, setOpenConversationMenuId] = useState(null);
  const [isApiDropdownOpen, setApiDropdownOpen] = useState(false);
  const [isChatActive, setChatActive] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [modal, setModal] = useState(null); // 'add-api', 'login', 'docs', 'user-menu'
  const [userName, setUserName] = useState("User");
  const [chatTitle, setChatTitle] = useState("New Conversation");
  const [form, setForm] = useState({ platform: 'Github', apiKey: '', rename: '' });
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const apiList = links.length ? links : DUMMY_APIS;

  // Auto-scroll to bottom of chat when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollTop = messagesEndRef.current.scrollHeight;
    }
  }, [messages]);

  // Fetch links on mount
  useEffect(() => {
    fetchLinks();
  }, []);

  const fetchLinks = async () => {
    try {
      const res = await axios.get(`${API_BASE}/links`);
      setLinks(res.data);
    } catch (e) { 
      console.error("Failed to fetch links:", e);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;
    
    const userMsg = input;
    setInput("");
    setChatActive(true);
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);
    
    try {
      const res = await axios.post(`${API_BASE}/chat`, { message: userMsg });
      // The server returns {answer, source_used, confidence_score}
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: res.data.answer,
        source: res.data.source_used,
        confidence: res.data.confidence_score
      }]);
    } catch (e) {
      console.error("Chat error:", e);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "Sorry, I encountered an error. Please check if the server is running." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const submitApi = async () => {
    if (!form.rename.trim()) {
      alert("Please provide a name for your connection");
      return;
    }
    try {
      await axios.post(`${API_BASE}/add-api`, form);
      fetchLinks();
      setModal(null);
      setForm({ platform: 'Github', apiKey: '', rename: '' });
    } catch (e) {
      console.error("Add API error:", e);
      alert("Failed to add API connection");
    }
  };

  const handleLogin = async () => {
    if (!loginEmail.trim()) {
      alert("Please enter your email");
      return;
    }
    try {
      const res = await axios.post(`${API_BASE}/login`, { 
        email: loginEmail, 
        password: loginPassword 
      });
      setUserName(res.data.name || loginEmail.split('@')[0]);
      setModal(null);
      setLoginEmail('');
      setLoginPassword('');
    } catch (e) {
      console.error("Login error:", e);
      // Fallback to local login
      setUserName(loginEmail.split('@')[0]);
      setModal(null);
      setLoginEmail('');
      setLoginPassword('');
    }
  };

  const startNewChat = () => {
    const id = Date.now();
    const title = `New Conversation ${conversations.length + 1}`;
    setConversations(prev => [{ id, title }, ...prev]);
    setActiveConversationId(id);
    setChatActive(false);
    setMessages([]);
    setChatTitle(title);
  };

  const selectLinkChat = (link, index) => {
    setChatActive(true);
    setChatTitle(`Chat with ${link.rename || link.platform}`);
    setMessages([{
      role: 'assistant',
      content: `Connected to ${link.platform}: ${link.rename}. Ask me anything about this data source.`,
      source: 'system',
      confidence: 1.0
    }]);
  };

  const selectConversation = (conversation) => {
    setActiveConversationId(conversation.id);
    setChatTitle(conversation.title);
    setChatActive(true);
    setOpenConversationMenuId(null);
  };

  const renameConversation = (conversationId) => {
    const target = conversations.find((item) => item.id === conversationId);
    if (!target) return;
    const renamed = window.prompt("Rename conversation", target.title);
    if (!renamed || !renamed.trim()) return;
    setConversations(prev =>
      prev.map(item =>
        item.id === conversationId ? { ...item, title: renamed.trim() } : item
      )
    );
    if (activeConversationId === conversationId) {
      setChatTitle(renamed.trim());
    }
    setOpenConversationMenuId(null);
  };

  const deleteConversation = (conversationId) => {
    if (conversations.length === 1) {
      alert("At least one conversation should exist.");
      setOpenConversationMenuId(null);
      return;
    }
    const remaining = conversations.filter(item => item.id !== conversationId);
    setConversations(remaining);
    if (activeConversationId === conversationId) {
      const fallback = remaining[0];
      setActiveConversationId(fallback.id);
      setChatTitle(fallback.title);
      setChatActive(false);
      setMessages([]);
    }
    setOpenConversationMenuId(null);
  };

  return (
    <div className="flex h-screen w-full bg-[#212121] text-white font-sans selection:bg-gray-500">
      
      {/* SIDEBAR */}
      <div className={`${isSidebarOpen ? 'w-64' : 'w-0'} bg-[#171717] transition-all duration-300 flex flex-col overflow-hidden border-r border-white/5`}>
        <div className="p-4 flex justify-between items-center">
          <button onClick={() => setSidebarOpen(false)} className="hover:bg-white/5 p-2 rounded-lg transition-colors">
            <PanelLeft size={20} />
          </button>
          <button onClick={startNewChat} className="hover:bg-white/5 p-2 rounded-lg transition-colors" title="New Chat">
            <Plus size={20}/>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto px-3">
          <h3 className="text-xs font-semibold text-gray-500 px-2 py-4 uppercase tracking-wider">Recents</h3>
          <div className="space-y-1">
            {conversations.map((conversation) => (
              <div 
                key={conversation.id}
                className={`group p-2 rounded-lg text-sm transition-colors ${activeConversationId === conversation.id ? 'bg-white/10' : 'hover:bg-white/5'}`}
              >
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => selectConversation(conversation)}
                    className="flex items-center gap-2 flex-1 min-w-0 text-left"
                  >
                    <MessageSquare size={14} className="text-gray-500 flex-shrink-0" />
                    <span className="truncate">{conversation.title}</span>
                  </button>
                  <div className="relative">
                    <button
                      onClick={() => setOpenConversationMenuId(openConversationMenuId === conversation.id ? null : conversation.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded-md transition"
                    >
                      <MoreHorizontal size={15} />
                    </button>
                    {openConversationMenuId === conversation.id && (
                      <div className="absolute right-0 top-8 z-20 w-36 bg-[#202020] border border-white/10 rounded-lg shadow-xl p-1">
                        <button
                          onClick={() => renameConversation(conversation.id)}
                          className="w-full text-left px-2 py-1.5 text-sm rounded-md hover:bg-white/10 flex items-center gap-2"
                        >
                          <Pencil size={14} /> Rename
                        </button>
                        <button
                          onClick={() => deleteConversation(conversation.id)}
                          className="w-full text-left px-2 py-1.5 text-sm rounded-md hover:bg-white/10 text-red-300 flex items-center gap-2"
                        >
                          <Trash2 size={14} /> Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* User Section (Bottom) - No "Free Plan" text after login */}
        <div className="p-3 border-t border-white/10">
          <button 
            onClick={() => setModal('user-menu')} 
            className="w-full flex items-center gap-3 p-2 hover:bg-white/5 rounded-xl transition-colors"
          >
            <div className="w-8 h-8 bg-orange-600 rounded-full flex items-center justify-center text-xs font-bold uppercase">
              {userName[0]}
            </div>
            <div className="text-left flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{userName}</p>
            </div>
          </button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col relative">
        {/* Toggle button if sidebar closed */}
        {!isSidebarOpen && (
          <button 
            onClick={() => setSidebarOpen(true)} 
            className="absolute top-4 left-4 z-10 p-2 hover:bg-white/5 rounded-lg transition-colors"
          >
            <PanelLeft size={20} />
          </button>
        )}

        {/* Top Header */}
        <div className={`h-14 flex items-center justify-start relative ${!isSidebarOpen ? 'pl-16' : 'px-4'}`}>
          <div className="relative">
          <button
            onClick={() => setApiDropdownOpen(!isApiDropdownOpen)}
            className="flex items-center gap-2 font-bold hover:bg-white/5 px-3 py-2 rounded-xl transition-colors text-lg"
          >
            Links <ChevronDown size={16} className="text-gray-400" />
          </button>
          {isApiDropdownOpen && (
            <div className="absolute left-0 top-12 z-30 w-72 bg-[#171717] border border-white/10 rounded-xl shadow-2xl p-2">
              <p className="text-xs text-gray-400 px-2 py-1">Connected APIs ({apiList.length})</p>
              {apiList.map((api, idx) => (
                <div key={`${api.rename}-${idx}`} className="px-2 py-2 rounded-lg hover:bg-white/5 flex items-center justify-between">
                  <span className="text-sm truncate">{api.rename}</span>
                  <span className="text-xs text-gray-500">{api.platform}</span>
                </div>
              ))}
            </div>
          )}
          </div>
          
          <button 
            onClick={() => setModal('add-api')}
            className="absolute right-4 border border-white/20 px-4 py-1.5 rounded-lg text-sm hover:bg-white/5 transition-colors flex items-center gap-2"
          >
            <Plus size={14} /> Add API
          </button>
        </div>

        {/* View Switcher */}
        <div ref={messagesEndRef} className="flex-1 overflow-y-auto flex flex-col items-center">
          {!isChatActive || messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full space-y-8 px-4">
              <h1 className="text-4xl md:text-5xl font-bold text-center">Multi-Tenant System</h1>
              <p className="text-gray-400 text-center max-w-md">
                Connect your APIs, scrape data, and chat with your connected sources using AI.
              </p>
              <div className="flex gap-4">
                <button 
                  onClick={() => setModal('docs')}
                  className="flex items-center gap-2 text-gray-400 hover:text-white underline decoration-gray-600 underline-offset-4 transition-colors"
                >
                  DOCUMENTATION <ExternalLink size={14}/>
                </button>
                <button 
                  onClick={() => setModal('add-api')}
                  className="flex items-center gap-2 text-gray-400 hover:text-white underline decoration-gray-600 underline-offset-4 transition-colors"
                >
                  ADD API CONNECTION <Plus size={14}/>
                </button>
              </div>
            </div>
          ) : (
            <div className="w-full max-w-3xl px-4 py-6 space-y-6 pb-32">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] ${m.role === 'user' ? '' : 'flex gap-3'}`}>
                    {m.role === 'assistant' && (
                      <img src="/Ahub.svg" alt="AI" className="w-8 h-8 rounded-full flex-shrink-0" />
                    )}
                    <div className={`p-4 rounded-2xl ${m.role === 'user' ? 'bg-white/10' : 'bg-[#2a2a2a]'}`}>
                      {m.content}
                      {m.source && (
                        <div className="mt-2 text-xs text-gray-500">
                          Source: {m.source} • Confidence: {(m.confidence * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex gap-3">
                    <img src="/Ahub.svg" alt="AI" className="w-8 h-8 rounded-full" />
                    <div className="bg-[#2a2a2a] p-4 rounded-2xl flex items-center gap-2">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input Box */}
        <div className="absolute bottom-0 left-0 right-0 p-4 pb-6 bg-gradient-to-t from-[#212121] via-[#212121] to-transparent">
          <div className="max-w-3xl mx-auto relative">
            <textarea 
              rows="1"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Ask anything..."
              className="w-full bg-[#2a2a2a] rounded-2xl p-4 pr-14 focus:outline-none focus:ring-1 focus:ring-white/20 resize-none overflow-hidden text-white placeholder-gray-500"
              style={{ minHeight: '52px' }}
            />
            <button 
              onClick={handleSendMessage}
              disabled={!input.trim() || isLoading}
              className="absolute right-3 bottom-3 p-2 bg-white text-black rounded-xl hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-center text-xs text-gray-500 mt-2">
            Multi-Tenant System  &middot; @KirtanDwivedi
          </p>
        </div>
      </div>

      {/* MODALS */}
      {modal === 'docs' && <DocsOverlay close={() => setModal(null)} />}
      
      {modal === 'add-api' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[#171717] border border-white/10 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Add Connection</h2>
              <button onClick={() => setModal(null)} className="text-gray-400 hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Platform</label>
                <select 
                  value={form.platform}
                  onChange={e => setForm({...form, platform: e.target.value})} 
                  className="w-full bg-[#2a2a2a] p-3 rounded-xl outline-none border border-white/10 focus:border-white/30 transition-colors"
                >
                  <option value="Github">GitHub</option>
                  <option value="Notion">Notion</option>
                  <option value="Discord">Discord</option>
                  <option value="StackOverflow">Stack Overflow</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">API Key</label>
                <input 
                  value={form.apiKey}
                  onChange={e => setForm({...form, apiKey: e.target.value})} 
                  type="password"
                  placeholder="Enter your API key"
                  className="w-full bg-[#2a2a2a] p-3 rounded-xl outline-none border border-white/10 focus:border-white/30 transition-colors" 
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Display Name</label>
                <input 
                  value={form.rename}
                  onChange={e => setForm({...form, rename: e.target.value})} 
                  placeholder="e.g., My Project Repo" 
                  className="w-full bg-[#2a2a2a] p-3 rounded-xl outline-none border border-white/10 focus:border-white/30 transition-colors" 
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button onClick={() => setModal(null)} className="px-4 py-2 hover:bg-white/5 rounded-xl transition-colors">Cancel</button>
                <button onClick={submitApi} className="bg-white text-black px-6 py-2 rounded-xl font-bold hover:bg-gray-200 transition-colors">Connect</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {modal === 'login' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[#171717] border border-white/10 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Login</h2>
              <button onClick={() => setModal(null)} className="text-gray-400 hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Email</label>
                <input 
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="your@email.com" 
                  className="w-full bg-[#2a2a2a] p-3 rounded-xl outline-none border border-white/10 focus:border-white/30 transition-colors" 
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Password</label>
                <input 
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••" 
                  className="w-full bg-[#2a2a2a] p-3 rounded-xl outline-none border border-white/10 focus:border-white/30 transition-colors" 
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button onClick={() => setModal(null)} className="px-4 py-2 hover:bg-white/5 rounded-xl transition-colors">Cancel</button>
                <button onClick={handleLogin} className="bg-white text-black px-6 py-2 rounded-xl font-bold hover:bg-gray-200 transition-colors">Login</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {modal === 'user-menu' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[#171717] border border-white/10 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Account</h2>
              <button onClick={() => setModal(null)} className="text-gray-400 hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
                <div className="w-10 h-10 bg-orange-600 rounded-full flex items-center justify-center text-sm font-bold uppercase">
                  {userName[0]}
                </div>
                <div>
                  <p className="font-medium">{userName}</p>
                  <p className="text-xs text-gray-400">Authenticated</p>
                </div>
              </div>
              <button 
                onClick={() => {
                  setModal('login');
                }} 
                className="w-full text-left p-3 hover:bg-white/5 rounded-xl flex items-center gap-3 transition-colors"
              >
                <User size={16}/> Switch Account
              </button>
              <button 
                onClick={() => {
                  setModal('docs');
                }} 
                className="w-full text-left p-3 hover:bg-white/5 rounded-xl flex items-center gap-3 transition-colors"
              >
                <ExternalLink size={16}/> Documentation
              </button>
              <button 
                onClick={() => setModal(null)} 
                className="w-full text-left p-3 hover:bg-white/5 rounded-xl flex items-center gap-3 mt-2 border-t border-white/10 pt-4 transition-colors"
              >
                <X size={16}/> Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}