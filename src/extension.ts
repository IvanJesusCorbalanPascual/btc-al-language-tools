import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export function activate(context: vscode.ExtensionContext) {
    const outputChannel = vscode.window.createOutputChannel('BTC AL Language Tools');
    context.subscriptions.push(outputChannel);

    // Registramos el comando principal que generará las traducciones
    let generateDisposable = vscode.commands.registerCommand('btc-translations.generate', async () => {
        
        // 1. Buscamos la carpeta del proyecto actual (el de Business Central)
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('Abre un proyecto de Business Central primero.');
            return;
        }
        const workspacePath = workspaceFolders[0].uri.fsPath;

        // 2. Gestionamos el archivo de configuración languages.json dentro de .vscode
        const vscodePath = path.join(workspacePath, '.vscode');
        if (!fs.existsSync(vscodePath)) {
            fs.mkdirSync(vscodePath, { recursive: true });
        }
        const languagesJsonPath = path.join(vscodePath, 'languages.json');
        if (!fs.existsSync(languagesJsonPath)) {
            const defaultLanguages = {
                "es": {"note_code": "ESP", "bcp47": "es-ES", "label": "Español"},
                "fr": {"note_code": "FRA", "bcp47": "fr-FR", "label": "Francés"},
                "de": {"note_code": "DEU", "bcp47": "de-DE", "label": "Alemán"}
            };
            
            try {
                fs.writeFileSync(languagesJsonPath, JSON.stringify(defaultLanguages, null, 4), 'utf-8');
                
                // Abrimos el archivo para que el usuario pueda modificarlo cómodamente
                const document = await vscode.workspace.openTextDocument(languagesJsonPath);
                await vscode.window.showTextDocument(document);
                
                vscode.window.showInformationMessage('Se ha creado el archivo languages.json. Por favor, configura los idiomas y vuelve a ejecutar el comando de traducción.');
                return; // Detenemos la ejecución para que configure antes de traducir
            } catch (err) {
                vscode.window.showErrorMessage(`Error al crear languages.json: ${err}`);
                return;
            }
        }

        // 3. Buscamos dónde está guardado nuestro script de Python dentro de la extensión
        const scriptPath = path.join(context.extensionPath, 'scripts', 'xlf_target_from_developer_note.py');

        // Validamos que exista la carpeta Translations y el archivo .g.xlf base
        const translationsPath = path.join(workspacePath, 'Translations');
        if (!fs.existsSync(translationsPath)) {
            vscode.window.showWarningMessage('No se ha encontrado la carpeta "Translations". Por favor, compila el proyecto primero (Ctrl+Shift+B) para que se genere automáticamente.');
            return;
        }

        const files = fs.readdirSync(translationsPath);
        const hasBaseXlf = files.some(f => f.endsWith('.g.xlf') && !f.match(/\.[a-z]{2}-[A-Z]{2}\.g\.xlf$/));
        if (!hasBaseXlf) {
            vscode.window.showWarningMessage('No se encontró ningún archivo .g.xlf base en "Translations". Asegúrate de tener la feature "TranslationFile" en app.json y compila el proyecto.');
            return;
        }

        // 4. Ejecutamos el script de Python de forma invisible
        vscode.window.showInformationMessage('Generando traducciones XLIFF...');
        
        // Le pasamos al script la ruta del proyecto actual para que busque la carpeta Translations
        const command = `python "${scriptPath}" -t "${path.join(workspacePath, 'Translations')}"`;
        
        cp.exec(command, { cwd: workspacePath }, (error: cp.ExecException | null, stdout: string, stderr: string) => {
            if (error) {
                vscode.window.showErrorMessage(`Error al traducir: ${stderr || error.message}`);
                return;
            }
            
            // Si todo va bien, mostramos un mensaje de éxito y un log en la consola
            vscode.window.showInformationMessage('¡Traducciones generadas con éxito!');
            outputChannel.clear();
            outputChannel.appendLine(stdout);
            outputChannel.show();
        });
    });

    // Registramos un comando adicional para inicializar/abrir la configuración fácilmente
    let initConfigDisposable = vscode.commands.registerCommand('btc-translations.initLanguages', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('Abre un proyecto de Business Central primero.');
            return;
        }
        const workspacePath = workspaceFolders[0].uri.fsPath;
        const vscodePath = path.join(workspacePath, '.vscode');
        if (!fs.existsSync(vscodePath)) {
            fs.mkdirSync(vscodePath, { recursive: true });
        }
        const languagesJsonPath = path.join(vscodePath, 'languages.json');
        
        if (!fs.existsSync(languagesJsonPath)) {
            const defaultLanguages = {
                "es": {"note_code": "ESP", "bcp47": "es-ES", "label": "Español"},
                "fr": {"note_code": "FRA", "bcp47": "fr-FR", "label": "Francés"},
                "de": {"note_code": "DEU", "bcp47": "de-DE", "label": "Alemán"}
            };
            fs.writeFileSync(languagesJsonPath, JSON.stringify(defaultLanguages, null, 4), 'utf-8');
            vscode.window.showInformationMessage('Archivo languages.json creado.');
        }
        
        // Abre el archivo en el editor
        const document = await vscode.workspace.openTextDocument(languagesJsonPath);
        await vscode.window.showTextDocument(document);
    });

    // Comando para generar un Codeunit de Test basado en el archivo actual
    let generateTestDisposable = vscode.commands.registerCommand('btc-translations.generateTest', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('Abre un archivo .al para generar su Test.');
            return;
        }

        const text = editor.document.getText();
        // Expresión regular para buscar la definición del objeto AL
        const match = text.match(/\b(table|tableextension|page|pageextension|codeunit|report|xmlport|query)\s+(\d+)\s+"?([^"\n{]+)"?/i);
        
        let objectType = 'Object';
        let objectName = 'Target';
        
        if (match) {
            objectType = match[1];
            objectName = match[3].trim();
        }

        // El nombre del Codeunit tiene un máximo de 30 caracteres en AL
        let testName = objectName.replace(/[^a-zA-Z0-9]/g, '');
        if (testName.length > 20) {
            testName = testName.substring(0, 20);
        }
        testName = testName + 'Test';

        const testCode = `codeunit 0 "${testName}"
{
    Subtype = Test;

    [Test]
    procedure Test${objectType}Visibility()
    begin
        // [SCENARIO] Comprobar comportamiento de ${objectType} "${objectName}"
        // [GIVEN] Precondiciones iniciales
        // [WHEN] Acción a realizar
        // [THEN] Resultado esperado
    end;
}
`;

        // Crear un nuevo documento sin guardar
        const document = await vscode.workspace.openTextDocument({
            language: 'al',
            content: testCode
        });
        
        await vscode.window.showTextDocument(document);
    });

    context.subscriptions.push(generateDisposable);
    context.subscriptions.push(initConfigDisposable);
    context.subscriptions.push(generateTestDisposable);
}

export function deactivate() {}