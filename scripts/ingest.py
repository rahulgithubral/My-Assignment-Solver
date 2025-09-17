"""
Document ingestion script for the Assignment Assistant Agent.
Processes documents and adds them to the vector store for RAG.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import List

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.rag import process_document, query_similar_documents, rag_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def ingest_documents(file_paths: List[str], assignment_id: str = None):
    """
    Ingest multiple documents into the vector store.
    
    Args:
        file_paths: List of file paths to ingest
        assignment_id: Optional assignment ID for metadata
    """
    logger.info(f"Starting ingestion of {len(file_paths)} documents")
    
    successful = 0
    failed = 0
    
    for file_path in file_paths:
        try:
            logger.info(f"Processing: {file_path}")
            
            result = await process_document(file_path, assignment_id)
            
            logger.info(f"Successfully processed {file_path}: {result['chunks_created']} chunks created")
            successful += 1
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            failed += 1
    
    logger.info(f"Ingestion complete: {successful} successful, {failed} failed")
    
    # Print store statistics
    stats = rag_system.get_store_stats()
    logger.info(f"Vector store now contains {stats['total_vectors']} vectors")


async def search_documents(query: str, k: int = 5):
    """
    Search for documents similar to the query.
    
    Args:
        query: Search query
        k: Number of results to return
    """
    logger.info(f"Searching for: '{query}'")
    
    try:
        results = await query_similar_documents(query, k)
        
        if not results:
            logger.info("No similar documents found")
            return
        
        logger.info(f"Found {len(results)} similar documents:")
        
        for i, result in enumerate(results, 1):
            logger.info(f"\n{i}. Score: {result['score']:.4f}")
            logger.info(f"   File: {result['file_path']}")
            logger.info(f"   Text: {result['text'][:200]}...")
            
            if result.get('assignment_id'):
                logger.info(f"   Assignment ID: {result['assignment_id']}")
    
    except Exception as e:
        logger.error(f"Search failed: {e}")


async def show_stats():
    """Show vector store statistics."""
    stats = rag_system.get_store_stats()
    
    print("\n=== Vector Store Statistics ===")
    print(f"Total vectors: {stats['total_vectors']}")
    print(f"Dimension: {stats['dimension']}")
    print(f"Store path: {stats['store_path']}")
    print(f"Metadata entries: {stats['metadata_entries']}")


def main():
    """Main function for the ingestion script."""
    parser = argparse.ArgumentParser(description="Document ingestion script for Assignment Assistant Agent")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest documents into vector store')
    ingest_parser.add_argument('files', nargs='+', help='File paths to ingest')
    ingest_parser.add_argument('--assignment-id', help='Assignment ID for metadata')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for similar documents')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--k', type=int, default=5, help='Number of results to return')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show vector store statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'ingest':
            asyncio.run(ingest_documents(args.files, args.assignment_id))
        elif args.command == 'search':
            asyncio.run(search_documents(args.query, args.k))
        elif args.command == 'stats':
            asyncio.run(show_stats())
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
