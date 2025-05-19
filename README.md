# Quarto Translator

This Python script batch-translates `.qmd` (Quarto Markdown) files from a source directory into a target language using the `deep-translator` package (Google Translate backend), while **preserving Markdown formatting**, including:

- Bold and italic text
- Inline code and code blocks
- Footnote references and definitions
- Callouts
- YAML front matter

It should work with markdown files and plain text files as well.

---

## 🚀 Features

- **Preserves formatting:** Inline code, footnotes, YAML headers, callouts, etc., are not broken during translation.
- **Intelligent processing:** Distinguishes between footnote references and definitions.
- **Handles emphasis:** Bold and italic text are translated properly, with spacing preserved.

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

## ⚙️ Configuration

You can change the target translation language at the top of the script:

```python
target_language = "en"  # Change this to any ISO 639-1 language code (e.g., "es", "de", "fr", "it")
```

---

## 📌 Notes

* Translation is done line-by-line with formatting placeholders.
* A delay (`time.sleep(0.3)`) is added between translations to avoid rate limiting.
* Only `.qmd` files in the `chapters/` directory will be processed.

---

## 🧪 Example

A line like this:

```markdown
This is **bold**, *italic*, and `inline_code`, with a footnote[^1].
```

Will be translated while keeping the format:

```markdown
Esto es **negrita**, *cursiva*, y `inline_code`, con una nota al pie[^1].
```

---

## 📝 License

This project is released under the MIT License.

