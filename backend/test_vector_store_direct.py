
import sys
import os

# Add backend to path
sys.path.append('g:/projects/tcs project/curabot/backend')

try:
    from knowledge.vector_store import VectorStore
    print("Initializing VectorStore...")
    vs = VectorStore()
    print("VectorStore initialized.")
    
    # Test heartbeat
    if vs.health_check():
        print("ChromaDB heartbeat OK.")
    else:
        print("ChromaDB heartbeat FAILED.")
        
    # Test embedding
    print("Testing embedding...")
    test_chunks = ["Patient has a history of hypertension."]
    count = vs.add_patient_records(
        user_id="test_user",
        report_id="test_report",
        source="test.pdf",
        chunks=test_chunks
    )
    print(f"Successfully indexed {count} chunks.")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
