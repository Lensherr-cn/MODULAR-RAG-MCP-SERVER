"""Test PDF ingestion.

This script tests the PDF document ingestion pipeline.
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


def test_pdf_ingestion():
    """Test PDF document ingestion."""
    print("=" * 60)
    print("Testing PDF Ingestion")
    print("=" * 60)

    # Check for PDF files
    docs_dir = project_root / "uploads"
    pdf_files = list(docs_dir.glob("*.pdf")) + list(docs_dir.glob("*.PDF"))

    if not pdf_files:
        print(f"ERROR: No PDF files found in {docs_dir}")
        return False

    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")

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

    # Process each PDF
    results = []
    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        try:
            trace = TraceContext(trace_type="ingestion")
            trace.metadata["source_path"] = str(pdf_path)
            result = pipeline.run(str(pdf_path), trace=trace)
            results.append((pdf_path.name, result))

            if result.success:
                print(f"  SUCCESS: {result.chunk_count} chunks, {result.image_count} images")
            else:
                print(f"  FAILED: {result.error}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append((pdf_path.name, None))

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
        print("\nPDF Ingestion Test: SUCCESS")
        return True
    else:
        print("\nPDF Ingestion Test: PARTIAL FAILURE")
        return False


if __name__ == "__main__":
    success = test_pdf_ingestion()
    sys.exit(0 if success else 1)
