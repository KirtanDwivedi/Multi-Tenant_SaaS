import React, { useState, useEffect, useRef } from 'react';
import { X, ArrowRight, Database, Zap, ShieldCheck } from 'lucide-react';

const NAV = [
  { id: 'overview',     label: 'Overview' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'langchain',    label: 'LangChain & RAG' },
  { id: 'connectors',   label: 'Connectors' },
  { id: 'api',          label: 'API Reference' },
  { id: 'chat',         label: 'Chat & Prompts' },
  { id: 'security',     label: 'Security' },
];

function Code({ children }) {
  return (
    <pre className="bg-[#171717] border border-white/10 rounded-xl px-5 py-4 text-sm font-mono text-gray-300 overflow-x-auto leading-relaxed my-4">
      <code>{children}</code>
    </pre>
  );
}

function InlineCode({ children }) {
  return (
    <code className="bg-white/10 text-white px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
  );
}

function Badge({ children, color = 'blue' }) {
  const map = {
    blue:   'bg-blue-500/15 text-blue-400 border-blue-500/20',
    green:  'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    yellow: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
    gray:   'bg-white/10 text-gray-400 border-white/10',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${map[color]}`}>
      {children}
    </span>
  );
}

function Dot({ status }) {
  const map = {
    yes:     ['bg-emerald-400', 'text-emerald-400', 'Live'],
    no:      ['bg-red-400',     'text-red-400',     'Pending'],
    limited: ['bg-yellow-400',  'text-yellow-400',  'Limited'],
  };
  const [dot, text, label] = map[status] || ['bg-gray-400','text-gray-400', status];
  return (
    <span className={`flex items-center gap-1.5 text-xs font-medium ${text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot} inline-block`} />{label}
    </span>
  );
}

function Section({ id, icon, title, subtitle, children }) {
  return (
    <section id={id} className="scroll-mt-24 pb-16 border-t border-white/10 pt-10 first:border-t-0 first:pt-0 last:pb-4">
      <div className="mb-7">
        <div className="flex items-center gap-3 mb-2">
          {icon && <span className="text-white">{icon}</span>}
          <h2 className="text-xl font-bold uppercase tracking-widest text-white">{title}</h2>
        </div>
        {subtitle && <p className="text-gray-400 text-sm leading-relaxed max-w-2xl mt-2">{subtitle}</p>}
      </div>
      {children}
    </section>
  );
}

function H3({ children }) {
  return <h3 className="text-xs font-semibold text-white mt-8 mb-3 uppercase tracking-widest opacity-80">{children}</h3>;
}

function P({ children }) {
  return <p className="text-gray-400 leading-relaxed text-sm mb-4">{children}</p>;
}

function Card({ icon, title, desc, tag }) {
  return (
    <div className="flex gap-3 p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition-colors">
      <div className="text-white mt-0.5 shrink-0">{icon}</div>
      <div>
        <div className="flex items-center gap-2 mb-1">
          <p className="text-white text-sm font-medium">{title}</p>
          {tag && <Badge color={tag.color}>{tag.label}</Badge>}
        </div>
        <p className="text-gray-400 text-xs leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

function DocTable({ headers, rows }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-white/10 my-5 bg-[#171717]/50">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 bg-white/5">
            {headers.map(h => (
              <th key={h} className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-widest text-gray-400 whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-3 text-gray-400 text-xs leading-relaxed">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Callout({ children, color = 'blue' }) {
  const map = {
    blue:   'border-blue-500/20 bg-blue-500/5 text-blue-300',
    yellow: 'border-yellow-500/20 bg-yellow-500/5 text-yellow-300',
    green:  'border-emerald-500/20 bg-emerald-500/5 text-emerald-300',
  };
  return (
    <div className={`border rounded-xl px-4 py-3 text-xs leading-relaxed my-4 ${map[color]}`}>
      {children}
    </div>
  );
}

export default function DocsOverlay({ close }) {
  const [active, setActive] = useState('overview');
  const observerRef = useRef(null);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) setActive(e.target.id); }),
      { rootMargin: '-15% 0px -70% 0px' }
    );
    NAV.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observerRef.current.observe(el);
    });
    return () => observerRef.current?.disconnect();
  }, []);

  const scrollTo = id => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div className="fixed inset-0 z-[200] bg-[#212121] overflow-y-auto animate-in slide-in-from-bottom-4 duration-500">
      
      {/* Fixed Close Button */}
      <button 
        onClick={close} 
        className="fixed top-8 right-8 z-[210] p-3 hover:bg-white/10 rounded-full transition-all text-gray-400 hover:text-white"
      >
        <X size={32} />
      </button>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 pt-32 pb-20">
        <h1 className="text-7xl md:text-8xl font-bold tracking-tighter mb-10 bg-gradient-to-b from-white to-gray-500 bg-clip-text text-transparent">
          Multi-Tenant System
        </h1>
        <p className="text-4xl md:text-6xl font-bold tracking-tighter mb-10 bg-gradient-to-b from-white to-gray-500 bg-clip-text text-transparent">
          Documentation
        </p>
        <p className="text-2xl md:text-3xl text-gray-400 font-light max-w-2xl leading-relaxed">
          The complete technical reference for the multi-tenant API connector and local RAG system.
        </p>
      </div>

      {/* Grid Layout Container */}
      <div className="max-w-7xl mx-auto px-6 flex flex-col lg:flex-row gap-14 pb-32">
        
        {/* Sticky Sidebar Navigation (Matches your original dark layout nicely) */}
        <aside className="hidden lg:block w-48 shrink-0">
          <nav className="sticky top-12 space-y-1">
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4 px-3">On this page</p>
            {NAV.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                  active === id 
                    ? 'bg-white/10 text-white font-medium shadow-sm' 
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Technical Documentation Modules */}
        <main className="flex-1 min-w-0 space-y-12">

          {/* OVERVIEW */}
          <Section
            id="overview"
            icon={<Database size={24} />}
            title="Overview"
            subtitle="A Single Page Application that connects to GitHub, Notion, Discord, and StackOverflow — scrapes their data into a local vector store — and lets an AI chatbot answer questions grounded entirely on that data."
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-6">
              <Card icon={<Database size={16}/>} title="Multi-Tenant APIs" desc="Connect GitHub, Notion, Discord, and StackOverflow from one dashboard." />
              <Card icon={<ShieldCheck size={16}/>} title="Privacy First" desc="All keys and scraped data stay in local JSON files. No external database." />
              <Card icon={<Zap size={16}/>} title="Gemini-Powered RAG" desc="gemini-1.5-flash answers questions grounded on your own connected data." tag={{ label: 'Live', color: 'green' }} />
              <Card icon={<ArrowRight size={16}/>} title="SPA Design" desc="Zero browser routing. State-driven overlays handle every page transition." />
            </div>

            <H3>Tech Stack</H3>
            <DocTable
              headers={['Layer', 'Technology']}
              rows={[
                ['Frontend',     'React + Vite · Tailwind CSS · Lucide Icons'],
                ['Backend',      'FastAPI (Python) · Uvicorn'],
                ['AI Model',     'Google Gemini — gemini-1.5-flash'],
                ['Embeddings',   'text-embedding-004 via LangChain GoogleGenAIEmbeddings'],
                ['Vector Store', 'ChromaDB (local persistent) · JSON fallback'],
                ['Storage',      'data.json · content.json · chroma_db/'],
              ]}
            />

            <H3>Theme Configuration</H3>
            <DocTable
              headers={['Token', 'Hex']}
              rows={[
                ['Main Background',    '#212121'],
                ['Sidebar Background', '#171717'],
                ['Input Background',   '#303030'],
              ]}
            />
          </Section>

          {/* ARCHITECTURE */}
          <Section
            id="architecture"
            icon={<Zap size={24} />}
            title="Architecture"
            subtitle="The UI responds instantly — ingestion runs down an independent background pipeline thread so your app workflow never drops frame updates."
          >
            <Code>{`[ FRONTEND — Add API ]
        │
        ▼
[ POST /api/add-api ]  ──►  1. Write metadata → data.json
        │
        ▼  BackgroundTasks
[ LangChain Loader ]  ──►  2. Deduplicate / incremental sync
        │
        ▼
[ RecursiveCharacterTextSplitter ]  ──►  3. chunk_size=600  overlap=60
        │
        ▼
[ Gemini text-embedding-004 ]  ──►  4. Vectorise chunks
        │
        ▼
[ ChromaDB  "tenant_knowledge" ]  ──►  5. Persist vectors + metadata`}</Code>

            <H3>Vector Datastore Structure</H3>
            <Code>{`{
  "vector":   [0.12, -0.43, 0.91, ...],   // 768-dim embedding
  "text":     "README content or Q&A...",
  "metadata": {
    "source_platform": "github",
    "display_name":    "My-Repo",
    "target_url":      "https://github.com/owner/repo",
    "harvested_at":    "2024-12-02T10:30:00Z"
  }
}`}</Code>

            <H3>RAG Context Construction Flow</H3>
            <Code>{`POST /api/chat
  → embed question         (text-embedding-004)
  → cosine search ChromaDB (top 3 chunks)
  → build context blocks   (with source headers)
  → Gemini gemini-1.5-flash (temperature 0.1)
  → return cited answer`}</Code>
          </Section>

          {/* LANGCHAIN & RAG */}
          <Section
            id="langchain"
            icon={<Database size={24} />}
            title="LangChain & RAG"
            subtitle="How raw pipeline connector records break down into token structures and get index-mapped into local data clusters."
          >
            <H3>Document Struct Assembly</H3>
            <P>
              LangChain converts raw inputs into schema-typed <InlineCode>Document</InlineCode> elements before pushing into the execution tree.
              The <InlineCode>metadata</InlineCode> dict map controls citation parsing in the downstream interface layer.
            </P>
            <Code>{`from langchain.schema import Document

Document(
  page_content = "Raw scraped text from GitHub README...",
  metadata = {
    "source_platform": "github",
    "display_name":    "My-Repo",
    "target_url":      "https://github.com/owner/repo",
    "harvested_at":    "2024-12-02T10:30:00Z"
  }
)`}</Code>

            <H3>Embedding Projections (text-embedding-004)</H3>
            <P>
              Gemini mathematical matrices index target contexts across a 768-dimensional float topology space.
              Matches optimize dynamically via standard vector coordinate calculations.
            </P>
            <Code>{`from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(
  model          = "models/text-embedding-004",
  google_api_key = GEMINI_API_KEY,
)

vector = embeddings.embed_query("What does this repo do?")
# → [0.12, -0.43, 0.91, ...]  768 numbers`}</Code>

            <H3>Chunk Strategy</H3>
            <P>Large text documents slice down structurally to protect the model's key attention thresholds while sliding window logic safeguards context boundary layers.</P>
            <Code>{`from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
  chunk_size    = 600,
  chunk_overlap = 60,
)
chunks = splitter.split_documents([document])`}</Code>

            <H3>ChromaDB Management Engine</H3>
            <P>
              Chroma processes local disk persistence arrays directly and isolates similarity calculations. 
              No extra operational backend dependencies needed.
            </P>
            <Code>{`import chromadb

client     = chromadb.PersistentClient(path="data/chroma_db/")
collection = client.get_or_create_collection("tenant_knowledge")

collection.add(
  ids        = ["chunk_001", "chunk_002", ...],
  documents  = [c.page_content for c in chunks],
  embeddings = [embeddings.embed_query(c.page_content) for c in chunks],
  metadatas  = [c.metadata for c in chunks],
)

# Retrieve top 3 closest chunks to a question
results = collection.query(
  query_embeddings = [embeddings.embed_query(user_question)],
  n_results        = 3,
)`}</Code>
            <Callout color="green">
              Chroma configuration applies standard <strong>Cosine similarity</strong> parameters out-of-the-box for highly accurate structural document extraction.
            </Callout>

            <H3>GitHub Webhooks & Async Sync Loops</H3>
            <P>
              System endpoints catch workspace events instantly to target active connections listed inside <InlineCode>data.json</InlineCode> 
              and dispatch clean index updates without human interaction.
            </P>
            <Code>{`# Payload GitHub sends on push
{
  "repository": { "html_url": "https://github.com/owner/repo" },
  "commits":    [...],
  "pusher":     { "name": "username" }
}

# FastAPI handler — server/main.py
@app.post("/api/webhooks/github")
async def github_webhook(payload: dict, background_tasks: BackgroundTasks):
    repo_url = payload.get("repository", {}).get("html_url")
    if repo_url in registered_urls:
        background_tasks.add_task(process_and_vectorize, repo_url)
    return { "status": "received" }`}</Code>
            <Callout color="yellow">
              Local configurations cannot interface directly with open webhooks. Use <strong>ngrok</strong> pipes to handle target development testing tunnels cleanly.
            </Callout>
          </Section>

          {/* CONNECTORS */}
          <Section
            id="connectors"
            icon={<Database size={24} />}
            title="Connectors"
            subtitle="Each target workspace maps directly to modular ingestion routines configured inside scrapers.py."
          >
            <DocTable
              headers={['Platform', 'Status', 'Data Retrieved']}
              rows={[
                ['GitHub',        <Dot status="limited" />, 'README via GitHub REST API'],
                ['StackOverflow', <Dot status="yes" />,     'Top 5 Q&A by tag via StackExchange API'],
                ['Notion',        <Dot status="limited" />,      'Block children recursive stitching'],
                ['Discord',       <Dot status="limited" />,      'Channel messages via Discord API'],
              ]}
            />

            <H3>scrape_github() Engine core</H3>
            <Code>{`async def scrape_github(repo_url: str, token: str = None):
    owner, repo = repo_url.rstrip("/").split("/")[-2:]
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/readme",
            headers=headers,
        )
    import base64
    return base64.b64decode(r.json()["content"]).decode("utf-8")`}</Code>

            <H3>scrape_stackoverflow() Engine core</H3>
            <Code>{`async def scrape_stackoverflow(tagged_topic: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.stackexchange.com/2.3/questions",
            params={
                "order": "desc", "sort": "votes",
                "tagged": tagged_topic,
                "site": "stackoverflow", "pagesize": "5",
            },
        )
    items = r.json().get("items", [])
    return "\\n".join(f"{q['title']} — {q['link']}" for q in items)`}</Code>

            <H3>Notion Recursive Block Assembly</H3>
            <P>
              The system crawls across parent blocks, matching paragraph items, listing parameters, and text pieces directly 
              into unified tracking streams stored cleanly inside <InlineCode>content.json</InlineCode>.
            </P>

            <H3>Manual Connection Ingestion Blueprint</H3>
            <Code>{`// server/data/data.json
{
  "platform":    "github",
  "apiKey":      "ghp_...",
  "displayName": "My Repo",
  "targetUrl":   "https://github.com/owner/repo",
  "rename":      "My Repo"
}`}</Code>
            <P>Simply save structural parameter additions and fire target extraction via the frontend system view.</P>

            <H3>Target Webhook Architecture</H3>
            <Code>{`# GitHub → Settings → Webhooks → Add webhook
Payload URL:  http://YOUR_NGROK_URL/api/webhooks/github
Content type: application/json
Events:       Just the push event`}</Code>
          </Section>

          {/* API REFERENCE */}
          <Section
            id="api"
            icon={<Zap size={24} />}
            title="API Reference"
            subtitle="Endpoints compile natively through FastAPI on port 8000. Access interactive sandboxes over /docs directly."
          >
            <DocTable
              headers={['Method', 'Endpoint', 'Description']}
              rows={[
                ['GET',    '/',                    'Server status + config flags'],
                ['GET',    '/api/links',           'Return all entries from data.json'],
                ['POST',   '/api/add-api',         'Save connection + fire background ingestion'],
                ['POST',   '/api/chat',            'RAG chat — returns Gemini answer with citations'],
                ['DELETE', '/api/link/{index}',    'Remove connection by array index'],
                ['GET',    '/api/content',         'Dump all stored RAG chunks'],
                ['POST',   '/api/login',           'Auth endpoint'],
                ['POST',   '/api/webhooks/github', 'GitHub push event → incremental re-sync'],
              ]}
            />

            <H3>POST /api/add-api</H3>
            <Code>{`// Request
{
  "platform":    "github" | "stackoverflow" | "notion" | "discord",
  "apiKey":      "your_token",
  "displayName": "My Connection",
  "targetUrl":   "https://github.com/owner/repo"
}
// Response — instant, ingestion runs in background
{ "status": "added", "message": "API connection saved. Ingestion started." }`}</Code>

            <H3>POST /api/chat</H3>
            <Code>{`// Request
{ "message": "What does this repo do?" }

// Response
{ "response": "According to your **GitHub (My-Repo)** data, this project..." }`}</Code>
          </Section>

          {/* CHAT & PROMPTS */}
          <Section
            id="chat"
            icon={<Zap size={24} />}
            title="Chat & Prompts"
            subtitle="Answers map entirely through localized datasets. The model completely ignores unverified external weights."
          >
            <H3>System Grounding Directives</H3>
            <Code>{`Role:
  Act as an elite, direct, developer-friendly internal RAG assistant.

Grounding Rule:
  Base answers strictly and exclusively on the text inside
  the reference context window provided below.

Absence Rule:
  If the context does not contain the answer, reply exactly:
  "Information not found in your connected application workspaces."

Inline Citations:
  Attribute every claim with a bold markdown source tag —
  "According to your **GitHub (My-Repo)** data, ..."

Context block format:
  [SOURCE_PLATFORM Workspace Layer (display_name)]
  <chunk text>`}</Code>

            <H3>Model Hyperparameters</H3>
            <Code>{`model:       gemini-1.5-flash
temperature: 0.1    // near-deterministic, factual
n_results:   3      // top 3 ChromaDB chunks used as context`}</Code>

            <H3>Source Prompt Matrix Locations</H3>
            <DocTable
              headers={['Location', 'File', 'Purpose']}
              rows={[
                ['Primary',   'server/main.py → _run_chat_inference', 'System prompt: grounding + absence + citation rules'],
                ['Secondary', 'server/main.py → _build_context_blocks', 'Labels each chunk with platform source headers'],
                ['Optional',  'server/prompts.py', 'Dedicated file for all prompt templates'],
              ]}
            />
          </Section>

          {/* SECURITY */}
          <Section
            id="security"
            icon={<ShieldCheck size={24} />}
            title="Security Architecture"
            subtitle="Three-layer filters ensure local secrets never cross verification logs or chat loops."
          >
            <DocTable
              headers={['Layer', 'File', 'Action']}
              rows={[
                ['1 — Scraping filter', 'server/scrapers.py', 'Skip .env, *.pem, credentials.json, secrets/ at crawl time'],
                ['2 — Pre-chunk filter', 'server/main.py → process_and_vectorize', 'Strip / redact before Document() wrapping'],
                ['3 — Prompt safety', 'server/main.py → _run_chat_inference', 'Never output secrets, API keys, or .env contents'],
              ]}
            />

            <Callout color="yellow">
              Ingestion scopes target top-level structural files initially. Keeping files protected at local source paths remains standard protocol.
            </Callout>

            <H3>Local Asset Allocation Layout</H3>
            <DocTable
              headers={['File', 'Contains']}
              rows={[
                ['server/data/data.json',                       'API connection metadata + keys (local only)'],
                ['server/data/chroma_db/fallback_vectors.json', 'Embedded chunks — json mode'],
                ['server/data/chroma_db/',                      'ChromaDB binary store — chromadb mode'],
              ]}
            />
          </Section>

        </main>
      </div>

      {/* Footer Decoration (Matches your beautiful original design) */}
      <div className="w-full bg-white text-black py-24 px-6 text-center">
        <h3 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">Ready to connect?</h3>
        <p className="text-gray-500 mb-8 text-lg max-w-md mx-auto">Add your first API and start chatting with your own data.</p>
        <button 
          onClick={close}
          className="bg-black text-white px-8 py-4 rounded-full font-bold inline-flex items-center gap-3 hover:scale-105 transition-transform"
        >
          Return to Dashboard <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}