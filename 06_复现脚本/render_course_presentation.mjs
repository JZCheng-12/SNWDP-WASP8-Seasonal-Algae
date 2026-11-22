/** Re-import a saved PPTX and render its slides; no scientific figures are redrawn.
 * Usage: node render_course_presentation.mjs INPUT_PPTX OUTPUT_DIRECTORY
 * Requires @oai/artifact-tool or ARTIFACT_TOOL_MODULE pointing to artifact_tool.mjs.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const [input, output] = process.argv.slice(2);
if (!input || !output) throw new Error('Usage: node render_course_presentation.mjs INPUT_PPTX OUTPUT_DIRECTORY');
const {PresentationFile, FileBlob} = await import(process.env.ARTIFACT_TOOL_MODULE
  ? pathToFileURL(path.resolve(process.env.ARTIFACT_TOOL_MODULE)).href : '@oai/artifact-tool');
await fs.mkdir(output, {recursive: true});
const existing = (await fs.readdir(output)).filter(n => /^slide-\d+\.png$/.test(n));
if (existing.length) throw new Error('Output directory already contains slide PNGs; use a fresh directory to avoid mixing previews.');
const presentation = await PresentationFile.importPptx(await FileBlob.load(input));
for (let i = 0; i < presentation.slides.items.length; i++) {
  const png = await presentation.export({slide: presentation.slides.items[i], format: 'png', scale: 1.5});
  await fs.writeFile(path.join(output, `slide-${String(i + 1).padStart(2, '0')}.png`), new Uint8Array(await png.arrayBuffer()));
}
console.log(`Rendered ${presentation.slides.items.length} saved slides to ${output}`);
