"""
Intelligent mode helpers with better AI interaction.
"""
import subprocess
import sys
import time

def smart_query(prompt, timeout=45, max_retries=2):
    """
    Call ollama with better error handling and retry logic.
    """
    for attempt in range(max_retries):
        try:
            # Using direct shell command to avoid  subprocess hanging
            import tempfile
            import os
            
            # Write prompt to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(prompt)
                temp_path = f.name
            
            try:
                # Run ollama with file input
                result = subprocess.run(
                    f"cat {temp_path} | ollama run qwen-lite 2>&1",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                os.unlink(temp_path)
                
                if result.stdout:
                    return result.stdout.strip()
                else:
                    return f"[No response - attempt {attempt + 1}]"
                    
            except subprocess.TimeoutExpired:
                os.unlink(temp_path)
                if attempt < max_retries - 1:
                    print(f"⏱ Timeout on attempt {attempt + 1}, retrying...")
                    time.sleep(2)
                else:
                    return "[Response timed out]"
            except Exception as e:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                return f"[Error: {str(e)[:50]}]"
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return f"[Fatal error: {str(e)[:50]}]"
    
    return "[Failed to get response after retries]"


def ask_clarifying_questions(topic, initial_info):
    """
    Ask 3-4 smart clarifying questions relevant to the topic.
    """
    questions_prompt = f"""Ask 3-4 specific, clarifying questions about this request to gather missing context:

TOPIC: {topic}
PROVIDED INFO: {initial_info}

Return ONLY the questions, numbered 1-4. Make them concrete and specific."""
    
    questions = smart_query(questions_prompt, timeout=30)
    return questions


def provide_context_summary(prompt_text):
    """
    Summarize key context from a longer prompt.
    """
    summary_prompt = f"""Summarize the key technical details and requirements from this:

{prompt_text[:500]}

Provide a 2-3 sentence summary of what's needed."""
    
    return smart_query(summary_prompt, timeout=25)
