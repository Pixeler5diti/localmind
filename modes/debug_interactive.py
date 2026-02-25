"""
Interactive debugging mode - allows multi-turn conversation.
Auto-loads files, provides solutions, and can apply fixes.
"""
from model import query
import json
from datetime import datetime
import os
import re
import shutil

def extract_and_read_files(text, work_dir="/home/diti/storage/localmind"):
    """
    Extract filenames from text and read their contents if they exist.
    Supports all code file types: .py, .js, .ts, .cpp, .c, .java, .sh, .rb, .go, etc.
    Looks for patterns like: filename.py, ./filename.js, etc.
    """
    file_contents = {}
    
    #lookin for common file names
    file_pattern = r'([.\w/-]*\.(?:py|js|ts|jsx|tsx|cpp|c|h|hpp|java|sh|bash|rb|go|rs|php|swift|kt|scala|cs|java|html|css|sql|json|yaml|yml|xml|gradle|maven|py))'
    filenames = re.findall(file_pattern, text)
    
    for filename in filenames:
        
        clean_name = filename.lstrip('./')
        full_path = os.path.join(work_dir, clean_name)
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    file_contents[clean_name] = content
                    print(f"📄 Found and loaded: {clean_name} ({len(content)} chars)")
            except Exception as e:
                print(f"⚠ Could not read {clean_name}: {e}")
    
    return file_contents

def apply_file_fix(filename, fixed_content, work_dir="/home/diti/storage/localmind", detect_language=True):
    """
    Apply a fix to a file by writing the corrected content.
    Creates a backup first.
    """
    full_path = os.path.join(work_dir, filename)
    
    if not os.path.exists(full_path):
        print(f" File not found: {full_path}")
        return False
    
    try:
        #  backup!!!
        backup_path = f"{full_path}.backup"
        shutil.copy2(full_path, backup_path)
        print(f"Backup created: {backup_path}")
        
        # Write fixed content
        with open(full_path, 'w') as f:
            f.write(fixed_content)
        
        print(f" Fixed: {filename}")
        return True
    except Exception as e:
        print(f" Could not apply fix: {e}")
        return False

def extract_code_blocks(text, language=None):
    """
    Extract code blocks from the AI response.
    Supports any language: ```python, ```js, ```cpp, etc.
    If language is specified, only extract that language's blocks.
    """
    if language:
        # findin language
        pattern = f'```{language}\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
    else:
        
        pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
    return matches

def get_file_language(filename):
    """
    Detect language from file extension.
    """
    ext_to_lang = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
        '.jsx': 'javascript', '.cpp': 'cpp', '.c': 'c', '.h': 'c', '.hpp': 'cpp',
        '.java': 'java', '.sh': 'bash', '.bash': 'bash', '.rb': 'ruby', '.go': 'go',
        '.rs': 'rust', '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
        '.scala': 'scala', '.cs': 'csharp', '.html': 'html', '.css': 'css',
        '.sql': 'sql', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
        '.xml': 'xml', '.gradle': 'gradle', '.maven': 'maven'
    }
    _, ext = os.path.splitext(filename)
    return ext_to_lang.get(ext, 'plaintext')

def prompt_to_apply_fix(filename, ai_response, file_contents):
    """
    Ask user if they want to apply the fix suggested by AI.
    Supports any code language.
    """
    language = get_file_language(filename)
    code_blocks = extract_code_blocks(ai_response, language)
    
    if not code_blocks:
        return False
    
    print("\n" + "="*70)
    print("🔧 FIX AVAILABLE")
    print("="*70)
    print(f"\nFile: {filename}")
    print(f"Fixed code preview:\n")
    print(code_blocks[0][:500])
    if len(code_blocks[0]) > 500:
        print("...[truncated]...\n")
    
    response = input("\n✋ Apply this fix to the file? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        if apply_file_fix(filename, code_blocks[0]):
            print("\n✨ File updated successfully!")
            return True
    else:
        print("\n⏭ Fix not applied. Continuing with session...\n")
        return False
    
    return False

def run_debug_session(initial_problem):
    """
    Start an interactive debugging session that keeps conversation open.
    Auto-detects and loads referenced Python files.
    """
    print("\n" + "="*70)
    print(" INTERACTIVE DEBUG SESSION")
    print("="*70)
    print(f"\nInitial Problem: {initial_problem}")
    
    # Auto-detecting files
    print("\n Scanning for referenced files...")
    file_contents = extract_and_read_files(initial_problem)
    
    if file_contents:
        print(f"\n Loaded {len(file_contents)} file(s) for context\n")
    
    print("\nType 'quit' to end session, or provide more details/answers to continue.\n")
    print("-"*70 + "\n")
    
    # Initial analysis being done
    file_context = ""
    if file_contents:
        file_context = "\n\nFILE CONTENTS LOADED:\n" + "-"*50 + "\n"
        for filename, content in file_contents.items():
            language = get_file_language(filename)
            file_context += f"\n📄 {filename}:\n```{language}\n{content}\n```\n"
    
    initial_prompt = f"""You are debugging this problem:

{initial_problem}{file_context}

STRATEGY:
1. Based on what you know, provide initial diagnosis (what's likely wrong)
2. Ask 2-3 SPECIFIC questions to confirm and gather critical details
3. Based on common patterns with this type of issue, suggest likely solutions
4. Format as:
   - ROOT CAUSE HYPOTHESIS (what you think it is)
   - IMMEDIATE ACTION ITEMS (what user should check/provide)
   - PRELIMINARY FIX (if you can guess the solution, provide with correct language syntax: ```python, ```js, ```cpp, etc.)
   - CRITICAL QUESTIONS (numbered 1-3)

IMPORTANT: When showing fixed code, wrap it in the correct language block (```python, ```javascript, ```cpp, etc.) so it can be auto-applied.
Support any programming language. Be ready to provide actual solutions once you have more info. Don't be vague."""
    
    print(" Analyzing problem & gathering details...\n")
    analysis = query(initial_prompt)
    print(analysis)
    print("\n" + "-"*70 + "\n")
    
    # keeping the agent convo alive
    conversation_history = [
        {"role": "assistant", "content": analysis},
        {"role": "user", "content": initial_problem}
    ]
    
    turn = 0
    max_turns = 10
    
    while turn < max_turns:
        turn += 1
        
        # Get user input
        try:
            user_input = input("Your response (or 'quit' to exit): ").strip()
        except EOFError:
            print("\n[Session ended]")
            break
        
        if user_input.lower() == 'quit':
            print("\n✓ Debug session closed.")
            break
        
        if not user_input:
            print("Please provide a response or 'quit' to exit.\n")
            continue
        
        # Add to history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Build context from conversation
        context = "\n".join([
            f"{'Assistant' if msg['role'] == 'assistant' else 'User'}: {msg['content'][:300]}..."
            for msg in conversation_history[-4:]  # Last 4 messages for context
        ])
        
        # Include file contents in every prompt for reference
        file_ref = ""
        if file_contents:
            file_ref = "\n\n FILE REFERENCES (for context):\n" + "-"*50 + "\n"
            for filename, content in file_contents.items():
                # Show relevant lines around the issue if possible
                language = get_file_language(filename)
                file_ref += f"\n{filename}:\n```{language}\n{content}\n```\n"
        
        # Continue debugging with context - FOCUS ON SOLVING
        continue_prompt = f"""Continue debugging and PROVIDE SOLUTIONS:

CONVERSATION SO FAR:
{context}

USER'S NEW INPUT: {user_input}{file_ref}

IMPORTANT: Now that you have more information, provide CONCRETE SOLUTIONS:
1. Diagnose the root cause based on all information
2. Provide step-by-step FIX (not just explanation)
3. When showing fixed code, ALWAYS wrap in ```python CODE ``` blocks (user can auto-apply)
4. Include code examples and explain WHY this fix works
5. List ways to prevent this in future
6. Ask what else they want to debug or if this resolved it

If you have enough info to solve it, SOLVE IT. Don't just ask more questions."""
        
        print("\n Analyzing...\n")
        response = query(continue_prompt)
        print(response)
        
        conversation_history.append({"role": "assistant", "content": response})
        
        # Check if there's a fix to apply
        if file_contents:
            for filename in file_contents.keys():
                # Check if this file is mentioned and there's a code block
                if filename in response and '```' in response:
                    print()
                    prompt_to_apply_fix(filename, response, file_contents)
                    # Reload file contents after potential fix
                    file_contents = extract_and_read_files(f"debug {filename}")
                    break
        
        # Check if user wants to continue
        print("\n" + "-"*70 + "\n")
        
        if turn >= max_turns - 1:
            print(" Max conversation turns reached!!. Session closing.")
            break
    
    print("\n" + "="*70)
    print("Debug session complete. Session saved to memory.")
    print("="*70 + "\n")
