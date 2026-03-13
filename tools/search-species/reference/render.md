# Render Module Reference

## 1. Input Constraints
* **⚠️ Image Locality (Strict)**: The searched 2D image MUST remain in the **exact same directory** as the `.json` file. **Do not move JSON files** from their original cache directory before rendering, otherwise the image will fall back to a placeholder.
* **Fault Tolerance**: Invalid or corrupted JSON paths are safely skipped without crashing.

## 2. Rendering Order & Control
* **Order Control**: The renderer aggregates multiple candidates into a single grid image. Cards are populated **strictly in the order the JSON file paths are passed in the CLI**. Order your arguments intentionally (e.g., pass the preferred or most reliable candidate first).

## 3. Displayed Data & Truncation
Cards visualize: Index, Source Engine, Name, Formula, Weight, and SMILES.
* **⚠️ SMILES Truncation**: Strings exceeding the max character limit (e.g., large macromolecules) are visually truncated to prevent layout breaks. The full SMILES is only preserved in the source `.json`.

## 4. Output
* **Return Value**: The CLI prints the *relative path* (from the current working directory) of the generated timestamped image (`renderResult_...png`). Use this path to deliver the final image to the user.
