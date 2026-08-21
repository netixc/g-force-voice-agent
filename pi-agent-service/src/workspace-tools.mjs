import { lstat, realpath } from "node:fs/promises";
import path from "node:path";

import {
  createEditToolDefinition,
  createFindToolDefinition,
  createGrepToolDefinition,
  createLsToolDefinition,
  createReadToolDefinition,
  createWriteToolDefinition,
} from "@earendil-works/pi-coding-agent";

const TOOL_FACTORIES = {
  read: createReadToolDefinition,
  grep: createGrepToolDefinition,
  find: createFindToolDefinition,
  ls: createLsToolDefinition,
  edit: createEditToolDefinition,
  write: createWriteToolDefinition,
};

export async function createWorkspaceToolDefinitions(workspace, toolNames) {
  const workspaceRoot = await realpath(workspace);
  return toolNames.map((name) => {
    if (name === "bash") {
      throw new Error(
        "The bash tool is disabled because it shares the Pi process credential boundary. Use a separate tool sandbox before enabling terminal execution.",
      );
    }
    const factory = TOOL_FACTORIES[name];
    if (!factory) throw new Error(`Unsupported workspace tool: ${name}`);
    const definition = factory(workspaceRoot);
    return {
      ...definition,
      execute: async (toolCallId, params, signal, onUpdate, context) => {
        await assertWorkspacePath(workspaceRoot, toolPath(name, params), name === "write");
        return definition.execute(toolCallId, params, signal, onUpdate, context);
      },
    };
  });
}

export async function assertWorkspacePath(workspaceRoot, requestedPath, allowMissing = false) {
  const root = await realpath(workspaceRoot);
  const candidate = path.resolve(root, requestedPath || ".");
  const resolved = allowMissing ? await resolveExistingAncestor(candidate) : await realpath(candidate);
  if (!isWithin(root, resolved)) {
    throw new Error(`Path is outside the mounted workspace: ${requestedPath || "."}`);
  }
  await rejectEscapingSymlinks(root, candidate, allowMissing);
  return candidate;
}

function toolPath(name, params) {
  if (name === "grep" || name === "find" || name === "ls") return params.path || ".";
  return params.path;
}

function isWithin(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

async function resolveExistingAncestor(candidate) {
  let current = candidate;
  while (true) {
    try {
      return await realpath(current);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
      const parent = path.dirname(current);
      if (parent === current) throw error;
      current = parent;
    }
  }
}

async function rejectEscapingSymlinks(root, candidate, allowMissing) {
  const relative = path.relative(root, candidate);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`Path is outside the mounted workspace: ${candidate}`);
  }

  let current = root;
  for (const segment of relative.split(path.sep).filter(Boolean)) {
    current = path.join(current, segment);
    try {
      const stats = await lstat(current);
      if (!stats.isSymbolicLink()) continue;
      const target = await realpath(current);
      if (!isWithin(root, target)) throw new Error(`Workspace symlink escapes the mounted workspace: ${current}`);
    } catch (error) {
      if (allowMissing && error?.code === "ENOENT") return;
      throw error;
    }
  }
}
