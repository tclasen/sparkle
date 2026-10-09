// Evaluation instrumentation, not a skill. Imported native tools retain their schemas.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
export default async function(pi: any) {
  const native = await import(pathToFileURL(process.env.SPARKLE_PI_TOOL_ENTRY!).href);
  const root = fs.realpathSync(process.cwd());
  const policy = JSON.parse(fs.readFileSync(process.env.SPARKLE_EVAL_POLICY!, 'utf8'));
  function resolve(p: string) {
    let absolute = path.resolve(root, p);
    let existing = absolute;
    while (!fs.existsSync(existing)) existing = path.dirname(existing);
    return path.resolve(fs.realpathSync(existing), path.relative(existing, absolute));
  }
  function check(p: string, write: boolean) {
    const absolute = resolve(p);
    if (!(absolute === root || absolute.startsWith(root + path.sep))) throw new Error('Evaluation boundary: outside workspace');
    if (write && policy.protected.some((p: string) => absolute === path.resolve(root,p) || absolute.startsWith(path.resolve(root,p)+path.sep))) throw new Error('Evaluation boundary: protected input/resource');
  }
  for (const make of [native.createReadToolDefinition, native.createWriteToolDefinition, native.createEditToolDefinition]) {
    const tool = make(root);
    const original = tool.execute;
    tool.execute = async (id: string, args: any, ...rest: any[]) => {
      check(args.path, tool.name !== 'read');
      return original(id,args,...rest);
    };
    pi.registerTool(tool);
  }
  pi.registerTool(native.createBashToolDefinition(root, {shellPath: process.env.SPARKLE_EVAL_SHELL, exposeSessionEnvironment:false,
    spawnHook: (ctx: any) => ({...ctx, env:{PATH:process.env.PATH, UV_CACHE_DIR:process.env.UV_CACHE_DIR, UV_OFFLINE:'1', PYTHONDONTWRITEBYTECODE:'1', TMPDIR:process.env.TMPDIR, LANG:'en_US.UTF-8'}})}));
}
