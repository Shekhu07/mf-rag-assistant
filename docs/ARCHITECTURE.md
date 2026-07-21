# 🏛️ ArthaAI System & Code Architecture

This document visually details the directory layout and the high-performance retrieval and serving pipelines implemented in the **ArthaAI Mutual Fund RAG Assistant**.

---

## 🏎️ 1. Runtime Request & RAG Data Flow

The diagram below maps how user inputs travel through the frontend, optimization gateways, hybrid retrieval engines, and AI generation layers.

```mermaid
flowchart TD
    User([User Browser]) <-->|1. HTTPS / WebSockets| Nginx[Nginx Reverse Proxy]
    Nginx <-->|2. Port 8501| Streamlit[Streamlit Frontend App]
    
    subgraph Streamlit Services
        Streamlit -->|Fetch live metrics| CacheNAV{NAV Cache <br/> TTL: 5 mins}
        CacheNAV -->|Cache Miss| AMFI[Public AMFI API]
        CacheNAV -->|Cache Hit| LocalNAV[Live NAV Metrics]
        
        Streamlit -->|Fetch feed & analyze| CacheNews{News Cache <br/> TTL: 30 mins}
        CacheNews -->|Cache Miss| GoogleNews[Google News RSS Feed]
        GoogleNews -->|Extract portfolio actions| GeminiNews[Gemini 2.5 Flash]
    end

    subgraph High-Performance RAG Pipeline
        Streamlit -->|User Query| Router{Intent Router Gateway}
        
        %% Intent Router Paths
        Router -->|A. Greetings / Thanks| GreetingResponse[Instant Greeting <br/> Latency: <0.1ms]
        Router -->|B. Direct Metric Lookups| MetricResponse[Offline Metadata Check <br/> Latency: <0.3ms]
        Router -->|C. Contextual Search| CacheCheck{Dual-Layer Semantic Cache}
        
        %% Caching Paths
        CacheCheck -->|Exact String Match| CacheHit1[Direct Cache Return <br/> Latency: <1.5ms]
        CacheCheck -->|Semantic Similarity >= 0.96| CacheHit2[Similarity Cache Return <br/> Latency: <425ms]
        CacheCheck -->|Cache Miss| Reformulator[Gemini Query Reformulator]
        
        %% Retrieval Layers
        Reformulator --> Embeddings[Google Text Embeddings v4]
        Embeddings --> QdrantDense[Qdrant Cosine Similarity]
        Reformulator --> BM25Sparse[BM25 Keyword Matching]
        
        %% Rank Blending
        QdrantDense -->|Dense Candidate Scores| RRF[Reciprocal Rank Fusion <br/> Rank Merger]
        BM25Sparse -->|Sparse Keyword Scores| RRF
        
        %% LLM Generation
        RRF -->|Top-k Grounded Context| LLM[Gemini 2.5 Flash Generation]
        LLM -->|Save Result| SaveCache[Store in Semantic Cache]
        SaveCache --> ChatResponse[Grounded Markdown Answer]
        
        %% Resilience Path
        LLM -.->|429 Rate Limited <br/> max_retries=0| Fallback[Local Metadata Fallback]
        Fallback --> ChatResponse
    end
    
    classDef boundary fill:#1e293b,stroke:#ffd700,stroke-width:2px,color:#fff;
    classDef process fill:#0f172a,stroke:#38bdf8,stroke-width:1px,color:#fff;
    classDef database fill:#1e1b4b,stroke:#a855f7,stroke-width:1px,color:#fff;
    classDef highlight fill:#78350f,stroke:#f59e0b,stroke-width:2px,color:#fff;
    
    class User boundary;
    class Nginx,Streamlit process;
    class QdrantDense,BM25Sparse,CacheCheck database;
    class RRF,Router highlight;
```

---

## 🗂️ 2. Physical File & Directory Architecture

The folder structure below maps the components on disk to their responsibilities in the architecture.

```mermaid
graph TD
    Root[mf-rag-assistant/] --> App[app.py <br/> Streamlit Dashboard & Chat UI]
    Root --> Docker[Dockerfile & docker-compose.yml <br/> Turnkey Production Containers]
    Root --> NginxConf[nginx_streamlit.conf <br/> Reverse Proxy / WS Upgrades]
    
    Root --> Src[src/ <br/> Core Modules]
    Src --> Config[config.py <br/> Constants & Chunk Limits]
    Src --> Ingest[ingest.py <br/> Ingestion & Qdrant Index creation]
    Src --> QueryEngine[query_engine.py <br/> Hybrid Search, RRF, Intent Router]
    Src --> Cache[semantic_cache.py <br/> Dual-Layer Caching Engine]
    Src --> Metadata[fund_metadata.py <br/> Offline Holdings & Fund Metrics]
    Src --> Utilities[utils.py & nav_service.py <br/> PDF Parsing & Concurrent Live NAV API]
    Src --> NewsService[news_service.py <br/> Google News RSS & Gemini Extraction]
    
    Root --> Data[data/ <br/> Scheme Factsheets]
    Data --> SBI[sbi_bluechip/ <br/> factsheet.pdf & returns_and_expenses.txt]
    Data --> PPF[parag_parikh_flexi/ <br/> factsheet.pdf]
    Data --> OtherFunds[...]
    
    Root --> VectorStore[vector_store/ <br/> Databases & Local Backups]
    VectorStore --> SQLite[qdrant_local/ <br/> Local file-backed Qdrant DB]
    VectorStore --> JsonCache[semantic_cache.json <br/> Serialized Cache Entries]
```
