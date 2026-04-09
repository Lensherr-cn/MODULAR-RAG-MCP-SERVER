"""Test document ingestion.

This script tests the multi-format document ingestion pipeline.
Supports: PDF, Markdown, Text, Word, Excel files.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from src.core.settings import load_settings
from src.ingestion.pipeline import IngestionPipeline
from src.core.trace import TraceContext
from src.libs.loader import LoaderFactory


def test_document_ingestion():
    """Test multi-format document ingestion."""
    print("=" * 60)
    print("Testing Multi-Format Document Ingestion")
    print("=" * 60)
    print(f"Supported formats: {LoaderFactory.supported_extensions()}")

    # Check for document files
    docs_dir = project_root / "uploads"

    # Find all supported files
    all_files = []
    for ext in LoaderFactory.supported_extensions():
        all_files.extend(docs_dir.glob(f"*{ext}"))
        all_files.extend(docs_dir.glob(f"*{ext.upper()}"))

    if not all_files:
        print(f"ERROR: No supported files found in {docs_dir}")
        return False

    print(f"\nFound {len(all_files)} file(s):")
    for f in all_files:
        print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    # Load settings
    try:
        settings = load_settings(project_root / "config" / "settings.yaml")
        print(f"\nSettings loaded successfully")
        print(f"  - Collection: {settings.vector_store.collection_name}")
    except Exception as e:
        print(f"ERROR loading settings: {e}")
        return False

    # Initialize pipeline
    try:
        pipeline = IngestionPipeline(
            settings=settings,
            collection="test_docs",
            force=True
        )
        print("Pipeline initialized successfully")
    except Exception as e:
        print(f"ERROR initializing pipeline: {e}")
        return False

    # Process each file
    results = []
    for file_path in all_files:
        print(f"\nProcessing: {file_path.name}")
        try:
            trace = TraceContext(trace_type="ingestion")
            trace.metadata["source_path"] = str(file_path)
            result = pipeline.run(str(file_path), trace=trace)
            results.append((file_path.name, result))

            if result.success:
                print(f"  SUCCESS: {result.chunk_count} chunks, {result.image_count} images")
            else:
                print(f"  FAILED: {result.error}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append((file_path.name, None))

    # Summary
    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)

    successful = sum(1 for _, r in results if r and r.success)
    total_chunks = sum(r.chunk_count for _, r in results if r and r.success)

    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print(f"Total chunks: {total_chunks}")

    if successful == len(results):
        print("\nDocument Ingestion Test: SUCCESS")
        return True
    elif successful > 0:
        print("\nDocument Ingestion Test: PARTIAL SUCCESS")
        return True
    else:
        print("\nDocument Ingestion Test: FAILED")
        return False


if __name__ == "__main__":
    success = test_document_ingestion()
    sys.exit(0 if success else 1)
