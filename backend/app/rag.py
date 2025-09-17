"""
RAG (Retrieval-Augmented Generation) module for document processing and vector search.
Handles document ingestion, text extraction, embedding generation, and similarity search.
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import hashlib
from datetime import datetime

# Document processing
import pypdf
from docx import Document as DocxDocument
import aiofiles

# Vector search
import faiss
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

# Embeddings
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document processing and text extraction."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from various document formats.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                return await self._extract_pdf_text(file_path)
            elif file_extension == '.docx':
                return await self._extract_docx_text(file_path)
            elif file_extension in ['.txt', '.md']:
                return await self._extract_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF files."""
        try:
            text_content = ""
            metadata = {}
            
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata = {
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                        "creator": pdf_reader.metadata.get("/Creator", ""),
                        "producer": pdf_reader.metadata.get("/Producer", ""),
                        "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
                        "modification_date": str(pdf_reader.metadata.get("/ModDate", ""))
                    }
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
                metadata["total_pages"] = len(pdf_reader.pages)
            
            return {
                "content": text_content.strip(),
                "metadata": metadata,
                "file_type": "pdf",
                "extraction_method": "pypdf"
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {e}")
            raise
    
    async def _extract_docx_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from DOCX files."""
        try:
            doc = DocxDocument(file_path)
            
            # Extract text from paragraphs
            text_content = ""
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            # Extract metadata
            metadata = {
                "title": doc.core_properties.title or "",
                "author": doc.core_properties.author or "",
                "subject": doc.core_properties.subject or "",
                "created": str(doc.core_properties.created) if doc.core_properties.created else "",
                "modified": str(doc.core_properties.modified) if doc.core_properties.modified else ""
            }
            
            return {
                "content": text_content.strip(),
                "metadata": metadata,
                "file_type": "docx",
                "extraction_method": "python-docx"
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting DOCX text: {e}")
            raise
    
    async def _extract_text_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text from plain text files."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
            
            return {
                "content": content.strip(),
                "metadata": {},
                "file_type": "text",
                "extraction_method": "direct_read"
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text file: {e}")
            raise


class TextChunker:
    """Handles text chunking for vector storage."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.logger = logging.getLogger(__name__)
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of text chunks with metadata
        """
        try:
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                
                # Try to break at sentence boundary
                if end < len(text):
                    last_period = chunk_text.rfind('.')
                    last_newline = chunk_text.rfind('\n')
                    break_point = max(last_period, last_newline)
                    
                    if break_point > start + self.chunk_size // 2:
                        chunk_text = text[start:start + break_point + 1]
                        end = start + break_point + 1
                
                chunk = {
                    "text": chunk_text.strip(),
                    "start_pos": start,
                    "end_pos": end,
                    "chunk_id": hashlib.md5(chunk_text.encode()).hexdigest()[:8],
                    "metadata": metadata or {}
                }
                
                chunks.append(chunk)
                start = end - self.chunk_overlap
                
                if start >= len(text):
                    break
            
            self.logger.info(f"Created {len(chunks)} chunks from text")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error chunking text: {e}")
            raise


class EmbeddingGenerator:
    """Generates embeddings for text chunks."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.google_client = None
        self.local_model = None
        
        # Initialize Google AI client if API key is available
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.google_client = genai
        
        # Initialize local model as fallback
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                self.logger.warning(f"Could not load local embedding model: {e}")
                self.local_model = None
        else:
            self.logger.warning("Sentence transformers not available, using simple embeddings only")
            self.local_model = None
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # Try Google AI first if available
            if self.google_client:
                try:
                    result = genai.embed_content(
                        model=settings.google_embedding_model,
                        content=text,
                        task_type="retrieval_document"
                    )
                    return result['embedding']
                except Exception as e:
                    self.logger.warning(f"Google AI embedding failed, falling back to local model: {e}")
            
            # Fallback to local model
            if self.local_model:
                embedding = self.local_model.encode(text)
                return embedding.tolist()
            
            # Last resort: simple TF-IDF-like embedding
            return self._generate_simple_embedding(text)
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise
    
    def _generate_simple_embedding(self, text: str) -> List[float]:
        """Generate a simple embedding as fallback."""
        # Simple word frequency-based embedding
        words = text.lower().split()
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Create a fixed-size embedding
        embedding_size = 128
        embedding = [0.0] * embedding_size
        
        for i, word in enumerate(sorted(word_freq.keys())):
            if i < embedding_size:
                embedding[i] = word_freq[word] / len(words)
        
        return embedding


class VectorStore:
    """Manages vector storage and similarity search using FAISS."""
    
    def __init__(self, store_path: str = None):
        self.store_path = store_path or settings.vector_store_path
        self.index = None
        self.metadata_store = []
        self.dimension = settings.embedding_dimension
        self.logger = logging.getLogger(__name__)
        
        # Create store directory
        Path(self.store_path).mkdir(parents=True, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index and metadata."""
        try:
            index_path = os.path.join(self.store_path, "faiss_index.bin")
            metadata_path = os.path.join(self.store_path, "metadata.json")
            
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                self.index = faiss.read_index(index_path)
                
                with open(metadata_path, 'r') as f:
                    self.metadata_store = json.load(f)
                
                self.logger.info(f"Loaded existing index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.metadata_store = []
                self.logger.info("Created new FAISS index")
                
        except Exception as e:
            self.logger.error(f"Error loading index: {e}")
            # Create new index on error
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata_store = []
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            index_path = os.path.join(self.store_path, "faiss_index.bin")
            metadata_path = os.path.join(self.store_path, "metadata.json")
            
            faiss.write_index(self.index, index_path)
            
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata_store, f, indent=2)
            
            self.logger.info(f"Saved index with {self.index.ntotal} vectors")
            
        except Exception as e:
            self.logger.error(f"Error saving index: {e}")
            raise
    
    def add_vectors(self, embeddings: List[List[float]], metadata_list: List[Dict[str, Any]]):
        """
        Add vectors and metadata to the store.
        
        Args:
            embeddings: List of embedding vectors
            metadata_list: List of metadata for each embedding
        """
        try:
            if not embeddings:
                return
            
            # Convert to numpy array
            vectors = np.array(embeddings, dtype=np.float32)
            
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(vectors)
            
            # Add to index
            self.index.add(vectors)
            
            # Add metadata
            self.metadata_store.extend(metadata_list)
            
            # Save to disk
            self._save_index()
            
            self.logger.info(f"Added {len(embeddings)} vectors to store")
            
        except Exception as e:
            self.logger.error(f"Error adding vectors: {e}")
            raise
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        try:
            if self.index.ntotal == 0:
                return []
            
            # Convert query to numpy array and normalize
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            
            # Search
            scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1:  # Valid result
                    result = {
                        "score": float(score),
                        "metadata": self.metadata_store[idx],
                        "index": int(idx)
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching vectors: {e}")
            raise


class RAGSystem:
    """Main RAG system that coordinates document processing, embedding, and search."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.document_processor = DocumentProcessor()
        self.text_chunker = TextChunker()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
    
    async def process_document(self, file_path: str, assignment_id: str = None) -> Dict[str, Any]:
        """
        Process a document and add it to the vector store.
        
        Args:
            file_path: Path to the document
            assignment_id: Optional assignment ID for metadata
            
        Returns:
            Dict containing processing results
        """
        try:
            self.logger.info(f"Processing document: {file_path}")
            
            # Extract text
            doc_data = await self.document_processor.extract_text(file_path)
            
            # Chunk text
            chunks = self.text_chunker.chunk_text(
                doc_data["content"],
                {
                    "file_path": file_path,
                    "assignment_id": assignment_id,
                    "file_type": doc_data["file_type"],
                    "metadata": doc_data["metadata"],
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            
            # Generate embeddings
            embeddings = []
            metadata_list = []
            
            for chunk in chunks:
                embedding = await self.embedding_generator.generate_embedding(chunk["text"])
                embeddings.append(embedding)
                
                chunk_metadata = {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "start_pos": chunk["start_pos"],
                    "end_pos": chunk["end_pos"],
                    **chunk["metadata"]
                }
                metadata_list.append(chunk_metadata)
            
            # Add to vector store
            self.vector_store.add_vectors(embeddings, metadata_list)
            
            return {
                "status": "success",
                "file_path": file_path,
                "chunks_created": len(chunks),
                "embeddings_generated": len(embeddings),
                "document_metadata": doc_data["metadata"]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    async def query_similar_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_generator.generate_embedding(query)
            
            # Search vector store
            results = self.vector_store.search(query_embedding, k)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "score": result["score"],
                    "text": result["metadata"]["text"],
                    "chunk_id": result["metadata"]["chunk_id"],
                    "file_path": result["metadata"]["file_path"],
                    "assignment_id": result["metadata"].get("assignment_id"),
                    "metadata": result["metadata"].get("metadata", {})
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error querying similar documents: {e}")
            raise
    
    def get_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "total_vectors": self.vector_store.index.ntotal,
            "dimension": self.vector_store.dimension,
            "store_path": self.vector_store.store_path,
            "metadata_entries": len(self.vector_store.metadata_store)
        }


# Global RAG system instance
rag_system = RAGSystem()


# Convenience functions for external use
async def process_document(file_path: str, assignment_id: str = None) -> Dict[str, Any]:
    """Process a document and add it to the vector store."""
    return await rag_system.process_document(file_path, assignment_id)


async def query_similar_documents(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Search for documents similar to the query."""
    return await rag_system.query_similar_documents(query, k)
