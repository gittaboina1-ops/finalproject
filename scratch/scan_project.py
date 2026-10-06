import os
import re

keywords = [
    'api_key', 'openai', 'gemini', 'google', 'anthropic', 'claude', 'groq',
    'huggingface', 'together', 'cohere', 'ollama', 'genai', 'OPENAI', 'GEMINI',
    'GOOGLE', 'ANTHROPIC', 'CLAUDE', 'GROQ', 'HF_TOKEN', 'TOGETHER', 'COHERE',
    'OPENROUTER', 'openrouter', 'llm', 'LLM', 'model'
]

pattern = re.compile('|'.join(keywords), re.IGNORECASE)

for root, dirs, files in os.walk('.'):
    if any(k in root for k in ['.git', 'node_modules', 'venv', '__pycache__', 'chroma_db', 'media', 'dist', 'images', 'scratch']):
        continue
    for file in files:
        if file.endswith(('.py', '.js', '.jsx', '.json', '.env', '.sh', '.md', '.html', '.txt')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                matches = []
                for idx, line in enumerate(lines):
                    if pattern.search(line):
                        clean_line = line.strip()
                        if 'KEY' in clean_line.upper() or 'SECRET' in clean_line.upper() or 'TOKEN' in clean_line.upper():
                            clean_line = re.sub(r'(=|:\s*)\s*[\'"]?[A-Za-z0-9_\-\.]{8,}[\'"]?', r'\1 [REDACTED_SECRET]', clean_line)
                        matches.append(f'  L{idx+1}: {clean_line}')
                if matches:
                    print(f'=== {path} ===')
                    for m in matches[:15]:
                        print(m)
                    if len(matches) > 15:
                        print(f'  ... and {len(matches)-15} more matches')
            except Exception as e:
                pass
