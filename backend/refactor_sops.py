import os

base_dir = r"c:\projects\tcs project\curabot\backend"
target_dirs = ["agents", "services", ""]

def replace_in_file(filepath, replacements):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                modified = True
                
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filepath}")
    except Exception as e:
        pass

# Step 1: Rename Conceptual SOPs in Prompts to RULES
conceptual_replacements = [
    ("SOP-001:", "RULE-01:"),
    ("SOP-002:", "RULE-02:"),
    ("SOP-003:", "RULE-03:"),
    ("SOP-004:", "RULE-04:"),
    ("SOP-005:", "RULE-05:"),
    ("SOP-002", "RULE-02"),
    ("SOP-005", "RULE-05"),
]

# Step 2: Rename Clinical SOPs to 001-015
clinical_replacements = [
    ("006", "001"),
    ("007", "002"),
    ("008", "003"),
    ("009", "004"),
    ("010", "005"),
    ("016", "006"),
    ("017", "007"),
    ("011", "008"),
    ("012", "009"),
    ("013", "010"),
    ("014", "011"),
    ("015", "012"),
    ("018", "013"),
    ("019", "014"),
    ("020", "015"),
]

# We need to be careful with clinical_replacements to only replace function names, comment references, and string names.
# So we map specifically:
exact_clinical_replacements = []
for old_num, new_num in clinical_replacements:
    exact_clinical_replacements.append((f"sop_{old_num}_", f"sop_{new_num}_"))
    exact_clinical_replacements.append((f"SOP-{old_num}", f"SOP-{new_num}"))
    exact_clinical_replacements.append((f"SOP {old_num}", f"SOP {new_num}"))
    exact_clinical_replacements.append((f"res_{old_num}", f"res_{new_num}"))
    exact_clinical_replacements.append((f"symptoms_{old_num}", f"symptoms_{new_num}"))
    exact_clinical_replacements.append((f"vitals_{old_num}", f"vitals_{new_num}"))

all_replacements = conceptual_replacements + exact_clinical_replacements

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.py') and not file == "refactor_sops.py":
            replace_in_file(os.path.join(root, file), all_replacements)

print("Refactor complete.")
