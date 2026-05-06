"""Fix: Remove orphaned emergency override code from orchestrator.py"""
with open("services/orchestrator.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find and remove lines 243-261 (0-indexed: 242-260)
# These are orphaned code starting with '"message"' after the SOP pipeline
new_lines = []
skip = False
for i, line in enumerate(lines):
    # Start skipping at the orphaned block (starts with the message line after sop_findings)
    if 'URGENT:**' in line and 'flags_str' in line and i > 240:
        skip = True
        continue
    if skip and line.strip() == '}':
        skip = False
        continue
    if skip:
        continue
    new_lines.append(line)

with open("services/orchestrator.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Cleaned up. Lines: {len(lines)} -> {len(new_lines)}")
