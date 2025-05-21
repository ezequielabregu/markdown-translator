import re
import time
from pathlib import Path
from deep_translator import GoogleTranslator

# Target language for translation. Example: "es" for Spanish, "fr" for French, etc.
TARGET_LANGUAGE = "es"
# Options: "qmd", "md", "txt"
FILE_EXTENSION = "md"  
# Directory containing the chapters to be translated
CHAPTERS_DIR = "chapters"


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

def extract_md_images_and_links(text):
    """Extract Markdown image and link syntax and replace with placeholders."""
    links = []
    
    # First handle images ![alt text](/path)
    def image_repl(match):
        alt_text = match.group(1)  # Text between ![...]
        url = match.group(2)       # URL between (...)
        
        # Only translate the alt text, keep URL as-is
        links.append({
            'type': 'image',
            'alt_text': alt_text,
            'url': url
        })
        return f"<<MDLINK_{len(links)-1}>>"
    
    # Then handle regular links [text](/path)
    def link_repl(match):
        link_text = match.group(1)  # Text between [...]
        url = match.group(2)        # URL between (...)
        
        links.append({
            'type': 'link',
            'text': link_text,
            'url': url
        })
        return f"<<MDLINK_{len(links)-1}>>"
    
    # Process images first (they start with !)
    text = re.sub(r'!\[(.*?)\]\((.*?)\)', image_repl, text)
    
    # Then process regular links
    text = re.sub(r'\[(.*?)\]\((.*?)\)', link_repl, text)
    
    return text, links

def restore_md_images_and_links(text, links):
    """Restore Markdown images and links with translated text but original URLs."""
    for idx, link_data in enumerate(links):
        if link_data['type'] == 'image':
            # For images, translate alt text only
            translated_alt = translate_text_fragment(link_data['alt_text'])
            # Reconstruct without spaces between components
            markdown = f"![{translated_alt}]({link_data['url']})"
        else:
            # For regular links, translate link text only
            translated_text = translate_text_fragment(link_data['text'])
            # Reconstruct without spaces between components
            markdown = f"[{translated_text}]({link_data['url']})"
        
        # Replace the placeholder with properly formatted markdown
        placeholder = f"<<MDLINK_{idx}>>"
        pattern = re.compile(r'<<\s*MDLINK_' + str(idx) + r'\s*>>', re.IGNORECASE)
        text = pattern.sub(markdown, text)
    
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
        target_lang = TARGET_LANGUAGE
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

def extract_callout_blocks(text):
    """Extract callout blocks with ALL their content, including any nested code blocks."""
    callouts = []
    
    # Match opening ::: tag, attributes, all content until closing ::: tag
    def callout_repl(match):
        callouts.append(match.group(0))
        return f"<<CALLOUT_{len(callouts)-1}>>"
    
    # Enhanced pattern that captures EVERYTHING between ::: {...} and ending :::
    # including any nested code blocks
    pattern = r':::\s*\{[^\}]+\}[\s\S]*?(?=\n:::)\n:::'
    text = re.sub(pattern, callout_repl, text)
    
    return text, callouts

def process_file(content):
    """Process a Quarto/Markdown file for translation while preserving formatting."""
    # 1. Extract COMPLETE callout blocks first
    content, callouts = extract_callout_blocks(content)
    
    # 2. Extract remaining code blocks (not in callouts)
    code_blocks = []
    def code_repl(match):
        code_blocks.append(match.group(0))
        return f"<<CODEBLOCK_{len(code_blocks)-1}>>"
    content = re.sub(r'```[\s\S]*?```', code_repl, content)

    # 3. Extract markdown images and links
    content, md_links = extract_md_images_and_links(content)

    # 4. Extract inline code
    content, inline_codes = extract_inline_code(content)

    # 5. Extract footnote references (not definitions)
    content, footnote_refs = extract_footnote_refs(content)

    # 6. Extract YAML frontmatter
    yaml = None
    yaml_match = re.match(r'^---[\s\S]*?---', content)
    if yaml_match:
        yaml = yaml_match.group(0)
        content = content.replace(yaml, "<<YAML>>")

    # 7. Process lines
    lines = content.split('\n')
    total_lines = len(lines)
    processed_lines = 0
    
    print(f"Starting translation of {total_lines} lines")
    
    for i, line in enumerate(lines):
        # Skip code, callout, yaml, empty, or lines with only placeholders
        if (line.strip().startswith('<<') and line.strip().endswith('>>')) or not line.strip():
            processed_lines += 1
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
            processed_lines += 1
            continue
        
        # Otherwise, translate bold/italic, then the line
        line2 = translate_bold_italic(line)
        line2 = fix_markdown_spacing(line2)
        lines[i] = translate_text_fragment(line2)
        processed_lines += 1
        
        # Update and display progress
        if processed_lines % 10 == 0 or processed_lines == total_lines:  # Update every 10 lines or at the end
            progress = (processed_lines / total_lines) * 100
            print(f"Progress: {progress:.1f}% ({processed_lines}/{total_lines})", end="\r")
    
    print("\nTranslation complete!")  # Add a newline after progress updates
    content = '\n'.join(lines)

    # 8. Restore everything in reverse order
    if yaml:
        content = content.replace("<<YAML>>", yaml)
    
    # Restore callouts and code blocks
    for idx, block in enumerate(callouts):
        content = content.replace(f"<<CALLOUT_{idx}>>", block)
    for idx, block in enumerate(code_blocks):
        content = content.replace(f"<<CODEBLOCK_{idx}>>", block)
    
    # Restore footnote references
    content = restore_footnote_refs(content, footnote_refs)
    
    # Restore markdown links and images
    content = restore_md_images_and_links(content, md_links)
    
    # Restore inline code LAST
    content = restore_inline_code(content, inline_codes)
    
    # Final cleanup for markdown spacing
    content = fix_markdown_spacing(content)
    
    return content

def main():
    """Main function to translate all Quarto files in the directory."""
    target_dir = Path(f"{CHAPTERS_DIR}.{TARGET_LANGUAGE}")
    target_dir.mkdir(exist_ok=True)
    source_dir = Path(CHAPTERS_DIR)
    
    # Ensure file extension has the correct format
    file_ext = FILE_EXTENSION.lstrip(".")
    
    # Find all files with the specified extension in the source directory
    files = list(source_dir.glob(f"*.{file_ext}"))
    total_files = len(files)
    
    print(f"Found {total_files} {file_ext} file(s) in {CHAPTERS_DIR}/")
    print("-" * 40)
    
    # Process each file
    for file_index, file_path in enumerate(files, 1):
        print(f"\nFile {file_index}/{total_files} ({(file_index/total_files)*100:.1f}%)")
        print(f"Translating: {file_path.name} → {file_path.stem}.{TARGET_LANGUAGE}.{file_ext}")
        print("-" * 40)
        
        try:
            # Read file content and immediately escape backslashes
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                content = file.read()
                
            # Replace Windows backslashes with double backslashes to escape them
            content = content.replace('\\', '\\\\')
            
            # Process the content as usual
            translated_content = process_file(content)
            
            # Restore single backslashes for the output file
            translated_content = translated_content.replace('\\\\', '\\')
            
            # Write result with the same extension
            target_file = target_dir / f"{file_path.stem}.{TARGET_LANGUAGE}.{file_ext}"
            with open(target_file, 'w', encoding='utf-8') as file:
                file.write(translated_content)
                
            print(f"✓ Completed: {file_path.name}")
            
        except Exception as e:
            print(f"✗ Error processing {file_path.name}: {str(e)}")
    
    print("\nAll translations completed!")

if __name__ == "__main__":
    main()