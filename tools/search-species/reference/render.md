# Render Module Reference

The `render` module is responsible for taking the structured JSON outputs from the search engines and converting them into a unified, human-readable visual gallery (grid of cards).

## 1. Input Handling & Dependencies
* **JSON-Driven**: The renderer takes paths to `.json` candidate files as its primary input.
* **⚠️ Image Locality (Strict Constraint)**: The module expects the associated 2D structure image to be located in the **exact same directory** as the `.json` file. **Do not move or isolate the JSON files** from their original output directory before rendering. If the image is not found alongside the JSON, the renderer will automatically fallback to an "Image Not Found" placeholder.
* **Fault Tolerance**: Invalid JSON paths or corrupted files are safely skipped with a warning. The rendering process will continue for the remaining valid candidates.

## 2. Card Layout & Grid System
Instead of generating individual image files for each candidate, the module aggregates them into a single comprehensive gallery image.
* **Grid Format**: Cards are arranged in a dynamic multi-column grid. The number of rows scales automatically based on the input count.
* **Card Structure**: Each card has a fixed layout containing:
  * **Left side**: A bounded area for the 2D molecular structure. Original images are proportionally scaled to fit without distortion.
  * **Right side**: A text area displaying the extracted metadata.

## 3. Displayed Data & Constraints
Each card visually displays the following properties:
1. Candidate Index
2. Source Engine (PubChem, OPSIN, or Wikidata)
3. Name
4. Formula
5. Weight (Relative Atomic Mass)
6. SMILES

**⚠️ Important Constraints (Data Truncation):**
To prevent text from breaking the visual layout, strings are strictly managed. Any single property string exceeding the maximum character limit is forcibly truncated. This is highly relevant for **SMILES** strings of large macromolecules, which may not be fully visible on the rendered card. (The complete SMILES is still preserved in the source JSON).

## 4. Output Convention
* **File Naming**: The final merged gallery image is saved using a timestamped format to prevent overwriting previous renders: 
  `renderResult_YYYYMMDDHHMMSS_{number_of_cards}.png`
* **Return Value**: Upon successful execution, the CLI prints the absolute path of the generated gallery image.