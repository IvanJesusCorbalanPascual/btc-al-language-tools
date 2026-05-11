# BTC AL Language Tools

Herramienta interna para automatizar la generación de archivos de traducción XLIFF en proyectos de Microsoft Dynamics 365 Business Central.

## ¿Qué hace esta extensión?
Esta extensión lee los archivos de traducción base (`.g.xlf`) de tu proyecto y rellena automáticamente las etiquetas `<target>` basándose en las notas de desarrollador (Developer Notes) que dejas en el código AL.

## ¿Cómo utilizarla?

1. **Añade notas en tu código AL:** 
   En los *labels* o textos de tu proyecto de Business Central, añade el texto traducido dentro de una etiqueta de comentario usando el código del idioma (`ESP=`, `DEU=`, `FRA=`, etc.).
   *Ejemplo:*
   ```al
   Caption = 'My Field', Comment = 'ESP="Mi Campo", DEU="Mein Feld"';
   ```

2. **Genera el archivo base (opcional):**
   Asegúrate de haber compilado tu proyecto de Business Central para que se genere el archivo `TuProyecto.g.xlf` en la carpeta `Translations/`.

3. **Ejecuta el comando de traducción:**
   - Abre la paleta de comandos de VS Code (`Ctrl + Shift + P` en Windows/Linux o `Cmd + Shift + P` en Mac).
   - Escribe y selecciona: **`BTC: Generar Traducciones XLIFF`**.

4. **Revisa el resultado:**
   - La extensión procesará el archivo base y generará automáticamente un archivo para cada idioma detectado (por ejemplo, `TuProyecto.es-ES.g.xlf`, `TuProyecto.de-DE.g.xlf`).
   - Se abrirá automáticamente el panel de "Salida" (Output) en la parte inferior de tu pantalla mostrándote un resumen de los idiomas encontrados y cuántas etiquetas se han traducido o se han omitido.

## Notas
- Para que funcione correctamente, el proyecto debe tener una carpeta llamada `Translations` con el archivo `.g.xlf` base dentro.
- Es necesario tener **Python** instalado en el sistema, ya que la extensión utiliza un script de Python en segundo plano para procesar rápidamente el XML.
- **Idiomas personalizados:** Puedes crear un archivo `languages.json` en la raíz de tu proyecto o dentro de la carpeta `Translations/` para definir tus propios idiomas, sobreescribiendo la configuración por defecto de la extensión.

---

## Agradecimientos

Un agradecimiento especial a **[Junpeng Jin](https://github.com/JJP00)**, compañero y colaborador, por su apoyo y aportaciones durante el desarrollo de esta extensión.
