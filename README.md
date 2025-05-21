# Quarto Translator

This Python script batch-translates .qmd (Quarto Markdown), .md (Markdown), or .txt (plain text) files from a source directory into a target language using the deep-translator package (Google Translate backend), while preserving Markdown formatting

---

## ⚙️ Configuration

1. Place your `.qmd` files in the `chapters/` directory. The script will process all files in this directory.

2. You can change the target translation language at the top of the script:

```python
# Target language for translation. Example: "es" for Spanish, "fr" for French, etc.
TARGET_LANGUAGE = "es"
# Options: "qmd", "md", "txt"
FILE_EXTENSION = "md"
# Directory containing the chapters to be translated
CHAPTERS_DIR = "chapters"
```

3. The script will create a new directory named `chapters.<lang>/` where `<lang>` is the target language code, and save the translated files there.

---

## 🚀 Features

- Preserves formatting: Inline code, footnotes, YAML headers, callouts, etc., are not broken during translation

- Intelligent processing: Distinguishes between footnote references and definitions

- Handles emphasis: Bold and italic text are translated properly, with spacing preserved

- Link preservation: URLs in links and image references are kept intact while translating alt text

- Progress tracking: Shows real-time translation progress for each file

- File format flexibility: Works with Quarto (.qmd), Markdown (.md), or plain text (.txt) files

---

## 🔧 Requirements

Install dependencies with:

```bash
pip install deep-translator
````

---

## 🛠️ Usage

Run the script directly:

```bash
python translate.py
```

Translated files will be saved in a folder named `chapters.<lang>/`, where `<lang>` is defined by the `target_language` variable.

---

## 📝 License

This project is released under the MIT License.
