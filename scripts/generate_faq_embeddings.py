"""
Pre-compute embeddings for FAQ documents.
Run this locally to generate embeddings JSON that gets deployed to Vercel.

Usage:
    python scripts/generate_faq_embeddings.py
"""
import os
import json
import re
from pathlib import Path
from typing import List, Dict

# Try to use Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Run: pip install google-generativeai")


def parse_faq_file(filepath: Path) -> List[Dict]:
    """Parse a FAQ markdown file into Q&A chunks."""
    content = filepath.read_text(encoding='utf-8')
    chunks = []
    
    # Extract topic from filename
    filename = filepath.stem
    topic_match = re.match(r'\d+_(.+)_FAQ', filename)
    topic = topic_match.group(1).replace('_', ' ') if topic_match else filename
    
    # Try to parse Q&A format
    # Pattern 1: ## Question / Answer pairs
    qa_pattern = r'##\s*Q\d*[:\.]?\s*(.+?)\n+(.*?)(?=##\s*Q|\Z)'
    matches = re.findall(qa_pattern, content, re.DOTALL)
    
    if matches:
        for i, (question, answer) in enumerate(matches):
            question = question.strip()
            answer = answer.strip()
            if question and answer:
                chunks.append({
                    "id": f"{filepath.stem}_q{i+1}",
                    "source": filepath.name,
                    "topic": topic,
                    "question": question,
                    "text": f"Question: {question}\n\nAnswer: {answer}",
                    "type": "qa"
                })
    
    # Pattern 2: Simple numbered Q&A
    if not chunks:
        simple_pattern = r'(?:^|\n)(\d+[\.\)]\s*.+?\?)\s*\n+(.*?)(?=\n\d+[\.\)]|\Z)'
        matches = re.findall(simple_pattern, content, re.DOTALL)
        
        for i, (question, answer) in enumerate(matches):
            question = question.strip()
            answer = answer.strip()
            if question and answer and len(answer) > 20:
                chunks.append({
                    "id": f"{filepath.stem}_q{i+1}",
                    "source": filepath.name,
                    "topic": topic,
                    "question": question,
                    "text": f"Question: {question}\n\nAnswer: {answer}",
                    "type": "qa"
                })
    
    # Fallback: Split into paragraphs
    if not chunks:
        paragraphs = content.split('\n\n')
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if len(para) > 50 and not para.startswith('#'):
                chunks.append({
                    "id": f"{filepath.stem}_p{i+1}",
                    "source": filepath.name,
                    "topic": topic,
                    "text": para,
                    "type": "paragraph"
                })
    
    return chunks


def get_embedding(text: str, model: str = "models/text-embedding-004") -> List[float]:
    """Get embedding using Google Gemini."""
    result = genai.embed_content(
        model=model,
        content=text[:2000],  # Limit text length
        task_type="retrieval_document"
    )
    return result['embedding']


def generate_embeddings():
    """Generate embeddings for all FAQ documents."""
    # Check for API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Set it with: set GOOGLE_API_KEY=your_key_here (Windows)")
        return
    
    if not GEMINI_AVAILABLE:
        print("Error: google-generativeai package not installed")
        return
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Find FAQ files
    faq_dir = Path("docs/childcare_faqs")
    if not faq_dir.exists():
        print(f"Error: FAQ directory not found: {faq_dir}")
        return
    
    faq_files = list(faq_dir.glob("*_FAQ.md"))
    print(f"Found {len(faq_files)} FAQ files")
    
    # Parse all FAQ documents
    all_chunks = []
    for faq_file in sorted(faq_files):
        print(f"  Parsing: {faq_file.name}")
        chunks = parse_faq_file(faq_file)
        all_chunks.extend(chunks)
        print(f"    -> {len(chunks)} chunks")
    
    print(f"\nTotal chunks: {len(all_chunks)}")
    
    # Generate embeddings
    print("\nGenerating embeddings...")
    embeddings = []
    
    for i, chunk in enumerate(all_chunks):
        try:
            embedding = get_embedding(chunk['text'])
            embeddings.append(embedding)
            print(f"  [{i+1}/{len(all_chunks)}] {chunk['id'][:30]}...")
        except Exception as e:
            print(f"  Error on chunk {chunk['id']}: {e}")
            # Use zero embedding as fallback
            embeddings.append([0.0] * 768)
    
    # Save to JSON
    output_file = Path("data/faq_embeddings.json")
    output_file.parent.mkdir(exist_ok=True)
    
    output_data = {
        "model": "text-embedding-004",
        "total_documents": len(all_chunks),
        "embedding_dim": len(embeddings[0]) if embeddings else 0,
        "documents": all_chunks,
        "embeddings": embeddings
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved embeddings to: {output_file}")
    print(f"   Documents: {len(all_chunks)}")
    print(f"   Embedding dim: {len(embeddings[0]) if embeddings else 0}")
    
    # Also create a lightweight version for Vercel
    lightweight_output = Path("api/faq_embeddings.json")
    with open(lightweight_output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False)  # No indent to save space
    
    print(f"   Also saved to: {lightweight_output}")


if __name__ == "__main__":
    generate_embeddings()
