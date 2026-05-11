# Change Log

All notable changes to the "BTC AL Language Tools" extension are documented in this file.

Format follows [Keep a Changelog](http://keepachangelog.com/).

## [1.0.0] - 2026-05-11

### Added
- **XLIFF Translation Automation** (`BTC: Generar Traducciones XLIFF`): Reads `.g.xlf` base files and auto-fills `<target>` tags from AL Developer Notes (e.g. `ESP="..."`, `DEU="..."`), generating one `.xlf` file per language.
- **Language Configuration** (`BTC: Configurar Idiomas de Traducción`): Creates and opens a `languages.json` file in the workspace `.vscode/` folder to let developers define custom target languages per project.
- **Test Codeunit Generator** (`BTC: Generar Codeunit de Test`): Generates a skeleton AL Test Codeunit based on the currently open `.al` object, following the standard [SCENARIO]/[GIVEN]/[WHEN]/[THEN] pattern.
- **AL Snippets**: Professional snippet library for Business Central development, covering Table/Page/Codeunit extensions and testing patterns.