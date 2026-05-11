# BTC AL Language Tools

**Productivity tools for Microsoft Dynamics 365 Business Central development in VS Code.**

Automate XLIFF translations, generate AL test codeunits and use professional code snippets — all without leaving the editor.

---

## Features

### 🌍 XLIFF Translation Automation

Automatically fills `<target>` tags in your `.g.xlf` translation files by reading **Developer Notes** embedded directly in your AL code.

**How it works:**

1. Add translations in your AL labels using language codes in the `Comment` field:
   ```al
   Caption = 'My Field', Comment = 'ESP="Mi Campo", DEU="Mein Feld", FRA="Mon Champ"';
   ```

2. Run **`BTC: Generar Traducciones XLIFF`** from the Command Palette (`Ctrl+Shift+P`).

3. The extension processes your `.g.xlf` base file and generates one translated file per language (e.g. `MyProject.es-ES.xlf`, `MyProject.de-DE.xlf`).

4. An **Output** panel shows a summary of languages detected and translations applied.

---

### ⚙️ Per-Project Language Configuration

Run **`BTC: Configurar Idiomas de Traducción`** to create a `languages.json` file inside your project's `.vscode/` folder.

This file lets you define which languages to target, fully customizable per project:

```json
{
    "es": { "note_code": "ESP", "bcp47": "es-ES", "label": "Español" },
    "fr": { "note_code": "FRA", "bcp47": "fr-FR", "label": "Francés" },
    "de": { "note_code": "DEU", "bcp47": "de-DE", "label": "Alemán" }
}
```

---

### 🧪 AL Test Codeunit Generator

Open any `.al` file and run **`BTC: Generar Codeunit de Test`** to instantly scaffold a test codeunit following the standard `[SCENARIO]/[GIVEN]/[WHEN]/[THEN]` pattern:

```al
codeunit 0 "MyObjectTest"
{
    Subtype = Test;

    [Test]
    procedure TestPageVisibility()
    begin
        // [SCENARIO] Check behavior of Page "My Object"
        // [GIVEN] Initial preconditions
        // [WHEN] Action is performed
        // [THEN] Expected result
    end;
}
```

---

### ✂️ AL Snippets

A professional snippet library for Business Central development, available in all `.al` files. Covers:

- Table & TableExtension patterns
- Page & PageExtension patterns
- Codeunit skeletons
- Test patterns with `[Test]` and `[HandlerFunctions]`

---

## Requirements

- **VS Code** `1.93.0` or higher
- **Python 3.x** must be installed and available in your system `PATH` (used internally for XML processing)
- A Business Central AL project with the `TranslationFile` feature enabled in `app.json`

---

## Extension Settings

This extension does not contribute VS Code settings. Configuration is managed via the `languages.json` file generated inside your project's `.vscode/` folder.

---

## Known Issues

- The translation command requires the project to be compiled first so that the `.g.xlf` base file exists in the `Translations/` folder.
- Python must be accessible from the terminal for the translation script to run.

---

## Release Notes

See [CHANGELOG](CHANGELOG.md) for a full history of changes.

---

## Acknowledgements

Special thanks to **[Junpeng Jin](https://github.com/JJP00)** for his support and contributions during the development of this extension.
