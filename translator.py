import re
import time
from pathlib import Path
from deep_translator import GoogleTranslator

CHAPTERS_DIR = "chapters"
target_language = "es"

def extract_footnote_refs(text):
    """Extract footnote references like [^exp_aleatorios-5] and replace with placeholders."""
    refs = []
    def repl(match):
        # Check if this is NOT part of a definition (not followed by colon)
        full_match = match.group(0)
        # Check if it's followed by a colon (definition marker)
        pos = match.end()
        if pos < len(text) and text[pos:].lstrip().startswith(':'):
            return full_match  # Don't replace definition markers
        refs.append(full_match)
        return f"<<FOOTNOTE_REF_{len(refs)-1}>>"
    
    text = re.sub(r'\[\^[^\]]+\]', repl, text)
    return text, refs

def restore_footnote_refs(text, refs):
    """Restore footnote references from placeholders."""
    for idx, ref in enumerate(refs):
        text = text.replace(f"<<FOOTNOTE_REF_{idx}>>", ref)
    return text

def extract_inline_code(text):
    """Extract inline code (e.g., `r emo::ji("rainbow")`) and replace with placeholders."""
    inline_codes = []
    
    # First handle inline code that might be within bold
    def code_repl(match):
        full_code = match.group(0)  # The entire match including backticks
        inline_codes.append(full_code)
        return f"<<INLINECODE_{len(inline_codes)-1}>>"
    
    # Match any text surrounded by backticks
    text = re.sub(r'`[^`]+`', code_repl, text)
    
    return text, inline_codes

def restore_inline_code(text, inline_codes):
    """Restore inline code from placeholders with robust handling for spacing variations."""
    for idx, code in enumerate(inline_codes):
        # Create a pattern that matches the placeholder with flexible spacing
        pattern = r'<<\s*INLINECODE_' + str(idx) + r'\s*>>'
        replacement = code
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def translate_bold_italic(text):
    """Process bold and italic text for translation."""
    # Bold
    def bold_repl(match):
        return f"**{translate_text_fragment(match.group(1))}**"
    
    # Italic
    def italic_repl(match):
        return f"*{translate_text_fragment(match.group(1))}*"
    
    # Process bold first (to handle **bold with *italic* inside**)
    text = re.sub(r'\*\*([^\*]+?)\*\*', bold_repl, text)
    
    # Then process italic (avoiding already processed bold markers)
    text = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', italic_repl, text)
    
    return text

def translate_text_fragment(text, target_lang=None):
    """Translate a text fragment."""
    if not text.strip():
        return text
    if target_lang is None:
        target_lang = target_language
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(text)
        time.sleep(0.3)  # Avoid rate limiting
        return translated if translated else text
    except Exception as e:
        print(f"Error translating: {str(e)[:100]}")
        return text

def fix_markdown_spacing(text):
    """Fix spacing issues in markdown formatting."""
    # Remove spaces after opening and before closing bold markers
    text = re.sub(r'\*\*\s*([^\*]+?)\s*\*\*', r'**\1**', text)
    
    # Remove spaces after opening and before closing italic markers
    text = re.sub(r'(?<!\*)\*\s*([^\*]+?)\s*\*(?!\*)', r'*\1*', text)
    
    return text

def process_file(content):
    """Process a Quarto/Markdown file for translation while preserving formatting."""
    # 1. Extract code blocks and callouts
    code_blocks = []
    callouts = []
    def code_repl(match):
        code_blocks.append(match.group(0))
        return f"<<CODEBLOCK_{len(code_blocks)-1}>>"
    def callout_repl(match):
        callouts.append(match.group(0))
        return f"<<CALLOUT_{len(callouts)-1}>>"
    content = re.sub(r'```[\s\S]*?```', code_repl, content)
    content = re.sub(r':::\s*\{[^\}]+\}[\s\S]*?:::', callout_repl, content)

    # 2. Extract inline code BEFORE extracting footnotes or other elements
    content, inline_codes = extract_inline_code(content)

    # 3. Extract footnote references (not definitions)
    content, footnote_refs = extract_footnote_refs(content)

    # 4. Extract YAML frontmatter
    yaml = None
    yaml_match = re.match(r'^---[\s\S]*?---', content)
    if yaml_match:
        yaml = yaml_match.group(0)
        content = content.replace(yaml, "<<YAML>>")

    # 5. Process lines
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Skip code, callout, yaml, empty, or lines with only placeholders
        if (line.strip().startswith('<<') and line.strip().endswith('>>')) or not line.strip():
            continue
        
        # Footnote definition: only translate after colon
        m = re.match(r'^(\[\^[^\]]+\]:|\<\<FOOTNOTE_REF_\d+\>\>:)(.*)', line)
        if m:
            marker, txt = m.groups()
            # Translate bold/italic in the content, then translate the content
            txt = translate_bold_italic(txt.strip())
            txt = fix_markdown_spacing(txt)
            txt = translate_text_fragment(txt)
            lines[i] = f"{marker} {txt}"
            continue
        
        # Otherwise, translate bold/italic, then the line
        line2 = translate_bold_italic(line)
        line2 = fix_markdown_spacing(line2)
        lines[i] = translate_text_fragment(line2)
    
    content = '\n'.join(lines)

    # 6. Restore everything in reverse order
    if yaml:
        content = content.replace("<<YAML>>", yaml)
    
    # Restore code blocks and callouts
    for idx, block in enumerate(code_blocks):
        content = content.replace(f"<<CODEBLOCK_{idx}>>", block)
    for idx, block in enumerate(callouts):
        content = content.replace(f"<<CALLOUT_{idx}>>", block)
    
    # Restore footnote references
    content = restore_footnote_refs(content, footnote_refs)
    
    # Restore inline code LAST, with robust pattern matching
    content = restore_inline_code(content, inline_codes)
    
    # Final cleanup for markdown spacing
    content = fix_markdown_spacing(content)
    
    return content

def main():
    """Main function to translate all Quarto files in the directory."""
    target_dir = Path(f"{CHAPTERS_DIR}.{target_language}")
    target_dir.mkdir(exist_ok=True)
    source_dir = Path(CHAPTERS_DIR)
    
    for file_path in source_dir.glob("*.qmd"):
        print(f"Translating: {file_path.name} → {file_path.stem}.{target_language}.qmd")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            translated_content = process_file(content)
            
            target_file = target_dir / f"{file_path.stem}.{target_language}.qmd"
            with open(target_file, 'w', encoding='utf-8') as file:
                file.write(translated_content)
                
        except Exception as e:
            print(f"✗ Error processing {file_path.name}: {str(e)}")
    
    print("Translation completed!")

if __name__ == "__main__":
    main()