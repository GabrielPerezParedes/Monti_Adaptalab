// Apply two small, guarded source hooks to the pinned public PhET checkout.
import { readFile, writeFile, mkdir, copyFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const target = resolve(process.argv[2] || '.phet/projectile-motion');
const marker = '// MONTI source adapter v1';
async function patch(relative, edits, base = target) {
  const path = resolve(base, relative);
  let text = await readFile(path, 'utf8');
  if (text.includes(marker)) return;
  for (const [before, after] of edits) {
    if (text.split(before).length !== 2) throw new Error(`Unexpected upstream source in ${relative}; inspect the pinned version before adapting it.`);
    text = text.replace(before, after);
  }
  await writeFile(path, `${marker}\n${text}`);
}
await patch('js/common/view/ProjectileMotionScreenView.ts', [
  ['  protected readonly cannonNode: CannonNode;', '  public readonly montiControls: { speed: NumberControl; target: TargetNode };\n  protected readonly cannonNode: CannonNode;'],
  ['    this.cannonNode = cannonNode;', '    this.montiControls = { speed: initialSpeedNumberControl, target: targetNode };\n    this.cannonNode = cannonNode;']
]);
await patch('js/intro/view/IntroScreenView.ts', [
  ["import Node from", "import installMontiBridge from '../../monti/installMontiBridge.js';\nimport Node from"],
  ['    this.projectileControlPanel = projectileControlPanel;', '    this.projectileControlPanel = projectileControlPanel;\n    installMontiBridge( model, { ...this.montiControls, viewProperties, projectileControlPanel } );']
]);
await mkdir(resolve(target, 'js/monti'), { recursive: true });
await copyFile(resolve(here, 'installMontiBridge.js'), resolve(target, 'js/monti/installMontiBridge.js'));
// The pinned 2026 build tools expect PhET's newer totality monorepo for metadata.
// These public split checkouts have individual SHAs instead. Record those honestly;
// do not stamp the MONTI repository's HEAD as though it were a PhET totality commit.
const work = dirname(target);
await copyFile(resolve(here, 'sources.lock.json'), resolve(work, 'monti-sources.lock.json'));
await patch('js/grunt/getCompatibleDependenciesJSON.ts', [[
  "    totality: {\n      sha: ( await gitImmutableExecute( [ 'rev-parse', 'HEAD' ], '..' ) ).trim(),\n      branch: 'HEAD'\n    }",
  "    ...Object.fromEntries( Object.entries( JSON.parse( readFileSync( '../monti-sources.lock.json', 'utf8' ) ).repositories ).map( ( [ name, source ]: [ string, any ] ) => [ name, { sha: source.sha, branch: 'HEAD' } ] ) )"
]], resolve(work, 'chipper'));
await patch('js/grunt/getBuildInfoJSON.ts', [[
  "    totalitySHA: ( await gitImmutableExecute( [ 'rev-parse', 'HEAD' ], '..' ) ).trim(),",
  "    totalitySHA: null,\n    sourceMode: 'public-split-repositories-with-monti-adapter',\n    sourceRepositories: JSON.parse( await fs.promises.readFile( '../monti-sources.lock.json', 'utf8' ) ).repositories,"
]], resolve(work, 'chipper'));
console.log('MONTI adapter applied to the pinned PhET source.');
