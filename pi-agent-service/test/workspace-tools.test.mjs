import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, rm, symlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { assertWorkspacePath, createWorkspaceToolDefinitions } from "../src/workspace-tools.mjs";

async function fixture() {
  const base = await mkdtemp(path.join(os.tmpdir(), "chief-os-tools-"));
  const workspace = path.join(base, "workspace");
  const outside = path.join(base, "outside");
  await mkdir(workspace);
  await mkdir(outside);
  await writeFile(path.join(workspace, "inside.txt"), "inside\n");
  await writeFile(path.join(outside, "secret.txt"), "secret\n");
  return { base, workspace, outside };
}

test("workspace paths accept files inside the root", async (t) => {
  const files = await fixture();
  t.after(() => rm(files.base, { recursive: true, force: true }));
  const resolved = await assertWorkspacePath(files.workspace, "inside.txt");
  assert.equal(resolved, path.join(files.workspace, "inside.txt"));
});

test("workspace paths reject absolute paths outside the root", async (t) => {
  const files = await fixture();
  t.after(() => rm(files.base, { recursive: true, force: true }));
  await assert.rejects(
    assertWorkspacePath(files.workspace, path.join(files.outside, "secret.txt")),
    /outside the mounted workspace/,
  );
});

test("workspace paths reject symlinks that escape the root", async (t) => {
  const files = await fixture();
  t.after(() => rm(files.base, { recursive: true, force: true }));
  await symlink(files.outside, path.join(files.workspace, "escape"));
  await assert.rejects(assertWorkspacePath(files.workspace, "escape/secret.txt"), /outside the mounted workspace/);
});

test("workspace paths reject new files outside the root", async (t) => {
  const files = await fixture();
  t.after(() => rm(files.base, { recursive: true, force: true }));
  await assert.rejects(
    assertWorkspacePath(files.workspace, "../outside/new.txt", true),
    /outside the mounted workspace/,
  );
});

test("wrapped read and write tools remain functional inside the workspace", async (t) => {
  const files = await fixture();
  t.after(() => rm(files.base, { recursive: true, force: true }));
  const [readTool, writeTool] = await createWorkspaceToolDefinitions(files.workspace, ["read", "write"]);
  const readResult = await readTool.execute("read-1", { path: "inside.txt" }, undefined, undefined, {});
  assert.equal(readResult.content[0].text, "inside\n");

  await writeTool.execute("write-1", { path: "created.txt", content: "created" }, undefined, undefined, {});
  assert.equal(await readFile(path.join(files.workspace, "created.txt"), "utf8"), "created");
});

test("bash is rejected until it has a separate sandbox", async (t) => {
  const files = await fixture();
  t.after(() => rm(files.base, { recursive: true, force: true }));
  await assert.rejects(createWorkspaceToolDefinitions(files.workspace, ["bash"]), /separate tool sandbox/);
});
