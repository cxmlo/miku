import json

# Read the transcript
with open('C:/Users/cxmluwu/.gemini/antigravity-ide/brain/21bb8ab9-a056-44a2-a73c-e6791e967c07/.system_generated/logs/transcript_full.jsonl', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print(f"Today's session started at line 993")
print("\n=== USER MESSAGES FROM YESTERDAY (before line 993) ===\n")

for i, line in enumerate(lines[:993]):
    try:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            content = data.get('content', '')[:300]
            print(f"--- Line {i} ({data.get('created_at', '')}) ---")
            print(content)
            print()
    except:
        pass
