import os

# Base directory is C:\projects\tcs project\curabot
base_dir = r"C:\projects\tcs project\curabot"
backend_dir = os.path.join(base_dir, "backend")
output_file = os.path.join(base_dir, "docs", "CuraBot_Full_Codebase_Dump.txt")

with open(output_file, 'w', encoding='utf-8') as outfile:
    outfile.write("CURABOT FULL SYSTEM CODEBASE CONTEXT\n")
    outfile.write("Paste this into Claude to provide deep, exact implementation details.\n\n")
    
    for root, dirs, files in os.walk(backend_dir):
        # Skip virtual environments, cache, and database folders
        if any(skip in root for skip in ['venv', '__pycache__', 'chroma_db', '.pytest_cache', 'synthetic_records']):
            continue
            
        for file in files:
            # We only want Python code and small JSON configs
            if file.endswith('.py') or file.endswith('.json'):
                filepath = os.path.join(root, file)
                
                # Skip huge json files (like database backups) to avoid breaking LLM token limits
                if file.endswith('.json') and os.path.getsize(filepath) > 300000:
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"FILE: {os.path.relpath(filepath, base_dir)} (Skipped: File too large for prompt context)\n")
                    outfile.write(f"{'='*80}\n\n")
                    continue

                outfile.write(f"\n{'='*80}\n")
                outfile.write(f"FILE: {os.path.relpath(filepath, base_dir)}\n")
                outfile.write(f"{'='*80}\n\n")
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    outfile.write(f"Error reading file: {e}\n")
                    
print(f"Dumped all code to {output_file}")
