# 📚 RAG (Retrieval-Augmented Generation) - Types and Usage

## 🎯 What is RAG?

**RAG** = Retrieval-Augmented Generation

It combines:
- **Retrieval**: Searching for relevant information from a knowledge base
- **Generation**: Using that information to generate accurate AI responses

**Why RAG?**
- ✅ LLMs have knowledge cutoff dates
- ✅ Can't access your private/company data
- ✅ May hallucinate without context
- ✅ RAG provides real-time, accurate information

---

## 🏗️ RAG Architecture Types

### 1. **Naive RAG** (Basic/Simple RAG)

**How it works:**
```
User Query → Embed Query → Search Vector DB → Retrieve Docs → Add to Prompt → LLM Response
```

**Characteristics:**
- Single retrieval step
- Simple embedding + search
- Direct context injection

**Use Cases:**
- FAQ systems
- Simple knowledge bases
- Document Q&A

**Pros:**
- ✅ Easy to implement
- ✅ Fast
- ✅ Good for simple queries

**Cons:**
- ❌ May miss relevant context
- ❌ No query refinement
- ❌ Limited for complex questions

**Example:**
```python
# Naive RAG Implementation
def naive_rag(query: str):
    # 1. Embed query
    query_embedding = embed(query)
    
    # 2. Search vector DB
    docs = vector_db.search(query_embedding, top_k=3)
    
    # 3. Create prompt with context
    context = "\n".join([doc.content for doc in docs])
    prompt = f"Context: {context}\n\nQuestion: {query}"
    
    # 4. Generate response
    response = llm.generate(prompt)
    return response
```

---

### 2. **Advanced RAG** (Multi-Step)

**How it works:**
```
User Query → Query Rewriting → Multi-Query Search → Re-ranking → Context Filtering → LLM Response
```

**Enhancements:**
- Query expansion
- Hypothetical document embeddings
- Re-ranking retrieved docs
- Context compression

**Use Cases:**
- Complex research questions
- Multi-topic queries
- Ambiguous questions

**Pros:**
- ✅ Better retrieval accuracy
- ✅ Handles complex queries
- ✅ More relevant context

**Cons:**
- ❌ Slower (multiple steps)
- ❌ More complex to implement
- ❌ Higher costs

**Example:**
```python
# Advanced RAG with Query Rewriting
def advanced_rag(query: str):
    # 1. Expand query into multiple variations
    query_variations = [
        query,
        rewrite_query_formal(query),
        rewrite_query_detailed(query)
    ]
    
    # 2. Search with all variations
    all_docs = []
    for q in query_variations:
        docs = vector_db.search(embed(q), top_k=5)
        all_docs.extend(docs)
    
    # 3. Re-rank documents
    ranked_docs = reranker.rank(query, all_docs, top_k=3)
    
    # 4. Compress context
    compressed_context = compress_docs(ranked_docs)
    
    # 5. Generate response
    prompt = f"Context: {compressed_context}\n\nQuestion: {query}"
    response = llm.generate(prompt)
    return response
```

---

### 3. **Agentic RAG** (Your VoiceBot Uses This!)

**How it works:**
```
User Query → Agent Decides → [Search Tool | RAG Tool | Other Tools] → Reasoning → Response
```

**Characteristics:**
- Agent **decides** when to use RAG
- Can call RAG multiple times
- Combines RAG with other tools
- Multi-step reasoning

**Use Cases:**
- Voice assistants
- Complex workflows
- Multi-domain questions

**Pros:**
- ✅ Intelligent tool selection
- ✅ Handles complex workflows
- ✅ Can use multiple sources

**Cons:**
- ❌ More complex
- ❌ Requires good prompting
- ❌ Can be slower

**Your Implementation:**
```python
# In your voice_agent.py
async def search_knowledge_base(self, query: str) -> str:
    """Agent decides to call this when needed"""
    # RAG implementation
    results = vector_db.search(query)
    return results
```

---

### 4. **Modular RAG** (Component-Based)

**How it works:**
```
User Query → [Retriever Module] → [Filter Module] → [Ranker Module] → [Generator Module]
```

**Characteristics:**
- Pluggable components
- Each module is swappable
- Mix and match strategies

**Use Cases:**
- Enterprise systems
- Custom pipelines
- A/B testing different strategies

**Example:**
```python
class ModularRAG:
    def __init__(self, retriever, filter, ranker, generator):
        self.retriever = retriever
        self.filter = filter
        self.ranker = ranker
        self.generator = generator
    
    def query(self, question: str):
        # Modular pipeline
        docs = self.retriever.retrieve(question)
        filtered = self.filter.filter(docs)
        ranked = self.ranker.rank(question, filtered)
        response = self.generator.generate(question, ranked)
        return response

# Swap components easily
rag = ModularRAG(
    retriever=DenseRetriever(),  # or SparseRetriever()
    filter=RelevanceFilter(),     # or SemanticFilter()
    ranker=CrossEncoderRanker(), # or ColBERTRanker()
    generator=LlamaGenerator()   # or GPT4Generator()
)
```

---

### 5. **Hybrid RAG** (Multi-Source)

**How it works:**
```
User Query → [Vector Search + Keyword Search + Graph Search] → Merge → Rank → Response
```

**Combines:**
- Dense retrieval (embeddings)
- Sparse retrieval (BM25)
- Knowledge graphs
- Structured data

**Use Cases:**
- Healthcare (structured + unstructured data)
- Legal (case law + documents)
- E-commerce (products + reviews)

**Example:**
```python
def hybrid_rag(query: str):
    # 1. Dense retrieval (semantic)
    semantic_docs = vector_db.search(embed(query), top_k=10)
    
    # 2. Sparse retrieval (keyword)
    keyword_docs = bm25_search(query, top_k=10)
    
    # 3. Graph search
    graph_docs = knowledge_graph.search(query, top_k=5)
    
    # 4. Merge and deduplicate
    all_docs = merge_deduplicate([semantic_docs, keyword_docs, graph_docs])
    
    # 5. Hybrid ranking
    ranked = hybrid_ranker(query, all_docs, top_k=5)
    
    # 6. Generate
    return llm.generate_with_context(query, ranked)
```

---

### 6. **Self-RAG** (Self-Reflective)

**How it works:**
```
User Query → Retrieve → Generate → Self-Critique → [Re-retrieve if needed] → Final Response
```

**Characteristics:**
- LLM evaluates its own output
- Decides if retrieval was helpful
- Can trigger re-retrieval

**Use Cases:**
- High-accuracy requirements
- Medical/legal domains
- Fact-checking systems

**Example:**
```python
def self_rag(query: str):
    # 1. Initial retrieval
    docs = retrieve(query)
    
    # 2. Generate response
    response = llm.generate(query, docs)
    
    # 3. Self-critique
    critique = llm.evaluate(f"""
        Question: {query}
        Retrieved Context: {docs}
        Generated Answer: {response}
        
        Is this answer supported by the context? (Yes/No)
        If No, suggest better retrieval query.
    """)
    
    # 4. Re-retrieve if needed
    if critique.needs_retrieval:
        new_docs = retrieve(critique.suggested_query)
        response = llm.generate(query, new_docs)
    
    return response
```

---

### 7. **Corrective RAG (CRAG)**

**How it works:**
```
User Query → Retrieve → Evaluate Relevance → [Good: Use | Bad: Web Search] → Response
```

**Characteristics:**
- Evaluates retrieval quality
- Falls back to web search if needed
- Corrects poor retrievals

**Use Cases:**
- Real-time information needs
- Incomplete knowledge bases
- Dynamic domains

**Example:**
```python
def corrective_rag(query: str):
    # 1. Retrieve from local KB
    docs = vector_db.search(query)
    
    # 2. Evaluate relevance
    relevance_score = evaluate_relevance(query, docs)
    
    if relevance_score > 0.7:
        # Good retrieval - use it
        return llm.generate(query, docs)
    else:
        # Poor retrieval - fall back to web search
        web_results = web_search(query)
        return llm.generate(query, web_results)
```

---

## 🎯 RAG Usage Scenarios

### **Scenario 1: Customer Support Bot**

**Best RAG Type:** Naive or Advanced RAG

**Use Case:**
- FAQ database
- Product documentation
- Troubleshooting guides

**Implementation:**
```python
# Customer support RAG
def support_rag(customer_query: str):
    # Search FAQ + docs + tickets
    faq_docs = search_faq(customer_query)
    doc_chunks = search_documentation(customer_query)
    similar_tickets = search_tickets(customer_query)
    
    # Combine and rank
    all_context = faq_docs + doc_chunks + similar_tickets
    ranked = rank_by_relevance(customer_query, all_context)
    
    # Generate response
    return llm.generate(f"""
        You are a helpful customer support agent.
        
        Context: {ranked[:3]}
        
        Customer Question: {customer_query}
        
        Provide a helpful, accurate response with step-by-step instructions if needed.
    """)
```

---

### **Scenario 2: Medical Diagnosis Assistant**

**Best RAG Type:** Self-RAG or Corrective RAG

**Use Case:**
- Medical literature search
- Symptom matching
- Treatment recommendations

**Implementation:**
```python
# Medical RAG with verification
def medical_rag(symptoms: str, patient_history: str):
    # Retrieve medical literature
    papers = search_pubmed(symptoms)
    guidelines = search_clinical_guidelines(symptoms)
    
    # Generate initial assessment
    assessment = llm.generate(f"""
        Symptoms: {symptoms}
        Patient History: {patient_history}
        Medical Literature: {papers}
        Guidelines: {guidelines}
        
        Provide differential diagnosis with confidence levels.
    """)
    
    # Verify with medical knowledge
    verification = verify_medical_accuracy(assessment)
    
    if not verification.accurate:
        # Re-retrieve with more specific query
        refined_docs = search_medical_db(verification.refined_query)
        assessment = llm.generate_with_verification(refined_docs)
    
    return assessment + "\n\n⚠️ Consult a healthcare professional for diagnosis."
```

---

### **Scenario 3: Legal Research Assistant**

**Best RAG Type:** Hybrid RAG

**Use Case:**
- Case law search
- Statute interpretation
- Legal precedent finding

**Implementation:**
```python
# Legal Hybrid RAG
def legal_rag(legal_query: str):
    # Search multiple sources
    case_law = search_case_law(legal_query)  # Vector search
    statutes = search_statutes_keyword(legal_query)  # Keyword search
    precedents = search_precedents_graph(legal_query)  # Graph search
    
    # Merge and rank by jurisdiction + relevance
    ranked = rank_legal_docs(
        query=legal_query,
        docs=[case_law, statutes, precedents],
        jurisdiction="US Federal"
    )
    
    # Generate legal analysis
    return llm.generate(f"""
        Legal Query: {legal_query}
        
        Relevant Case Law: {ranked['cases']}
        Applicable Statutes: {ranked['statutes']}
        Precedents: {ranked['precedents']}
        
        Provide legal analysis with citations.
    """)
```

---

### **Scenario 4: E-Commerce Product Recommendations**

**Best RAG Type:** Hybrid RAG + Agentic

**Use Case:**
- Product search
- Personalized recommendations
- Review analysis

**Implementation:**
```python
# E-commerce RAG
def ecommerce_rag(user_query: str, user_profile: dict):
    # Multi-source retrieval
    products = search_products_semantic(user_query)  # Vector DB
    reviews = search_reviews_keyword(user_query)     # Text search
    user_history = get_user_purchase_history(user_profile)
    similar_users = find_similar_users(user_profile)
    
    # Collaborative filtering + content-based
    recommendations = hybrid_recommender(
        query=user_query,
        products=products,
        reviews=reviews,
        user_history=user_history,
        similar_users=similar_users
    )
    
    # Generate personalized response
    return llm.generate(f"""
        User is looking for: {user_query}
        User preferences: {user_profile}
        
        Top recommended products:
        {recommendations}
        
        Reviews highlight:
        {summarize_reviews(reviews)}
        
        Provide personalized product recommendations with reasoning.
    """)
```

---

### **Scenario 5: Code Documentation Assistant**

**Best RAG Type:** Modular RAG

**Use Case:**
- Code search
- API documentation
- Examples retrieval

**Implementation:**
```python
# Code RAG
def code_rag(coding_question: str):
    # Search code repositories
    code_examples = search_github(coding_question)
    
    # Search documentation
    api_docs = search_api_docs(coding_question)
    
    # Search Stack Overflow
    so_answers = search_stackoverflow(coding_question)
    
    # Rank by code quality + relevance
    ranked_code = rank_code_examples(
        query=coding_question,
        examples=code_examples,
        criteria=['correctness', 'readability', 'best_practices']
    )
    
    # Generate code solution
    return llm.generate(f"""
        Question: {coding_question}
        
        API Documentation: {api_docs}
        Example Code: {ranked_code[0]}
        Community Solutions: {so_answers}
        
        Provide a code solution with:
        1. Working code example
        2. Explanation
        3. Best practices
    """)
```

---

## 🏢 Enterprise RAG Patterns

### **Pattern 1: Multi-Tenant RAG**

```python
# Each customer has isolated RAG
class MultiTenantRAG:
    def __init__(self):
        self.tenant_databases = {}
    
    def query(self, tenant_id: str, question: str):
        # Isolate by tenant
        tenant_db = self.get_tenant_db(tenant_id)
        docs = tenant_db.search(question)
        return llm.generate(question, docs)
```

### **Pattern 2: Hierarchical RAG**

```python
# Documents organized in hierarchy
def hierarchical_rag(query: str):
    # First search high-level summaries
    summaries = search_summaries(query)
    
    # Then drill down to relevant sections
    relevant_section = summaries[0].section_id
    detailed_docs = search_section(relevant_section, query)
    
    return llm.generate(query, detailed_docs)
```

### **Pattern 3: Streaming RAG**

```python
# Stream results as they're found
async def streaming_rag(query: str):
    # Start retrieval
    docs_stream = vector_db.search_stream(query)
    
    # Generate response as docs arrive
    async for doc in docs_stream:
        partial_response = llm.generate_streaming(query, doc)
        yield partial_response
```

---

## 🛠️ Implementation for Your VoiceBot

### Current Setup
Your VoiceBot already has **Agentic RAG** built-in:

```python
# In src/agents/voice_agent.py
@tool
async def search_knowledge_base(self, query: str) -> str:
    """Search knowledge base (RAG)."""
    # This is called by the agent when needed
    start_time = time.time()
    
    try:
        # RAG implementation
        results = self.rag_system.search(query)
        duration = time.time() - start_time
        
        return f"Found: {results}"
    except Exception as e:
        return f"Error: {e}"
```

### Upgrade to Advanced RAG

Create `src/rag/advanced_rag.py`:

```python
from typing import List
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

class AdvancedRAG:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="llama3.1:8b")
        self.vector_store = Chroma(
            persist_directory="./data/chroma_db",
            embedding_function=self.embeddings
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
    
    def add_documents(self, documents: List[str]):
        """Add documents to knowledge base"""
        chunks = self.text_splitter.split_documents(documents)
        self.vector_store.add_documents(chunks)
    
    def search(self, query: str, top_k: int = 3):
        """Advanced search with query enhancement"""
        # 1. Expand query
        expanded_queries = self.expand_query(query)
        
        # 2. Search with all queries
        all_results = []
        for q in expanded_queries:
            results = self.vector_store.similarity_search(q, k=top_k)
            all_results.extend(results)
        
        # 3. Re-rank
        ranked = self.rerank(query, all_results)
        
        # 4. Return top results
        return ranked[:top_k]
    
    def expand_query(self, query: str) -> List[str]:
        """Expand query into variations"""
        return [
            query,
            f"How to {query}",
            f"What is {query}",
            f"Explain {query}"
        ]
    
    def rerank(self, query: str, docs: List):
        """Simple reranking by relevance"""
        # Could use cross-encoder here
        return sorted(docs, key=lambda d: self.relevance_score(query, d), reverse=True)
    
    def relevance_score(self, query: str, doc) -> float:
        """Calculate relevance score"""
        # Simple scoring - could be enhanced
        query_terms = set(query.lower().split())
        doc_terms = set(doc.page_content.lower().split())
        overlap = len(query_terms & doc_terms)
        return overlap / len(query_terms)
```

---

## 📊 Comparison Table

| RAGType | Complexity | Speed | Accuracy | Use Case |
|---------|------------|-------|----------|----------|
| Naive RAG | ⭐ | ⚡⚡⚡ | ⭐⭐ | Simple FAQ |
| Advanced RAG | ⭐⭐⭐ | ⚡⚡ | ⭐⭐⭐⭐ | Complex queries |
| Agentic RAG | ⭐⭐⭐⭐ | ⚡⚡ | ⭐⭐⭐⭐ | Multi-tool systems |
| Modular RAG | ⭐⭐⭐ | ⚡⚡ | ⭐⭐⭐⭐ | Custom pipelines |
| Hybrid RAG | ⭐⭐⭐⭐ | ⚡ | ⭐⭐⭐⭐⭐ | Multi-source data |
| Self-RAG | ⭐⭐⭐⭐⭐ | ⚡ | ⭐⭐⭐⭐⭐ | High accuracy needs |
| CRAG | ⭐⭐⭐ | ⚡⚡ | ⭐⭐⭐⭐ | Fallback needed |

---

## 🚀 Getting Started

### 1. Choose Your RAG Type
Based on your use case:
- **Simple FAQ** → Naive RAG
- **Voice Assistant** → Agentic RAG (you have this!)
- **Research Tool** → Advanced or Hybrid RAG
- **High Stakes** → Self-RAG or CRAG

### 2. Implement
See code examples above for your chosen type.

### 3. Optimize
- Monitor retrieval quality
- A/B test different strategies
- Measure response accuracy

---

## 📚 Resources

- **LangChain RAG** - https://python.langchain.com/docs/use_cases/question_answering/
- **LlamaIndex** - https://docs.llamaindex.ai/
- **RAG Papers** - Search "Retrieval-Augmented Generation" on arXiv
- **Vector Databases** - Chroma, Pinecone, Weaviate, Qdrant

---

## Next Steps for Your VoiceBot

1. **Add documents to your knowledge base**
2. **Test the RAG tool** with actual queries
3. **Monitor performance** with timing metrics
4. **Upgrade to Advanced RAG** if needed

Your VoiceBot is ready for RAG! 🚀
