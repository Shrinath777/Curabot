import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

env_path = str(Path(__file__).resolve().parent / ".env")
load_dotenv(dotenv_path=env_path, override=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.supabase_client import supabase_service
from knowledge.vector_store import VectorStore

async def sync_records():
    print("Initializing VectorStore...")
    vs = VectorStore()
    
    if not getattr(supabase_service, "client", None):
        print("Error: Supabase client is not initialized. Please configure .env properly.")
        return
        
    print("Fetching medical reports from Supabase...")
    res = supabase_service.client.table('medical_reports').select('id, user_id, report_type, extracted_text, file_url').execute()
    reports = res.data
    
    if not reports:
        print("No medical reports found in Supabase.")
        return
        
    print(f"Found {len(reports)} total medical reports. Rebuilding local embeddings...")
    
    total_chunks = 0
    for r in reports:
        text = r.get('extracted_text', '')
        if not text:
            print(f"Skipping report {r.get('id')} - no extracted text.")
            continue
            
        chunks = []
        current_chunk = ""
        for line in text.split('\n'):
            if len(current_chunk) + len(line) > 600:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)
            
        print(f"Embedding {len(chunks)} chunks for report {r.get('id')}...")
        chunks_added = vs.add_patient_records(
            user_id=r.get('user_id'),
            report_id=r.get('id'),
            source=r.get('file_url', r.get('report_type', 'Recovered PDF')),
            chunks=chunks
        )
        total_chunks += chunks_added
        
    print(f"\n✅ Success! Synchronized {len(reports)} cloud medical reports into {total_chunks} local vector chunks in ChromaDB.")

if __name__ == "__main__":
    asyncio.run(sync_records())
