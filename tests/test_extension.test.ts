/**
 * Tests for CLI-Anything Pi extension command registration.
 *
 * Verifies that all 5 commands are registered, handlers invoke
 * sendUserMessage with the expected content, and edge cases are handled.
 *
 * Run with: npx vitest run tests/test_extension.test.ts
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ─── Types ────────────────────────────────────────────────────────────

interface RegisteredCommand {
	name: string;
	options: {
		description: string;
		handler: (args: string, ctx: MockContext) => Promise<void>;
		getArgumentCompletions?: (prefix: string) => Array<{ value: string; label: string }> | null;
	};
}

interface MockContext {
	ui: {
		notify: ReturnType<typeof vi.fn>;
	};
}

interface MockPi {
	registerCommand: ReturnType<typeof vi.fn>;
	sendUserMessage: ReturnType<typeof vi.fn>;
	registeredCommands: RegisteredCommand[];
	sentMessages: string[];
}

// ─── Mock Pi Extension API ────────────────────────────────────────────

function createMockPi(): MockPi {
	const registeredCommands: RegisteredCommand[] = [];
	const sentMessages: string[] = [];

	return {
		registerCommand: vi.fn((name: string, options: RegisteredCommand["options"]) => {
			registeredCommands.push({ name, options });
		}),
		sendUserMessage: vi.fn((msg: string) => {
			sentMessages.push(msg);
		}),
		registeredCommands,
		sentMessages,
	};
}

// ─── Mock file system for readAsset ───────────────────────────────────

const MOCK_HARNESS = "# HARNESS.md Mock\nTest harness content.";
const MOCK_COMMANDS: Record<string, string> = {
	"cli-anything.md": "# cli-anything command mock",
	"refine.md": "# refine command mock",
	"test.md": "# test command mock",
	"validate.md": "# validate command mock",
	"list.md": "# list command mock",
};

vi.mock("node:fs", () => ({
	readFileSync: (path: string, _encoding: string) => {
		const p = String(path);
		if (p.endsWith("HARNESS.md")) return MOCK_HARNESS;
		for (const [name, content] of Object.entries(MOCK_COMMANDS)) {
			if (p.endsWith(join("commands", name))) return content;
		}
		throw new Error(`ENOENT: no such file or directory, open '${p}'`);
	},
}));

// ─── Helper ───────────────────────────────────────────────────────────

async function loadExtension() {
	const extPath = join(__dirname, "..", "index.ts");
	const mod = await import(extPath);
	return mod;
}

// ─── Tests ────────────────────────────────────────────────────────────

describe("CLI-Anything Extension", () => {
	let mockPi: MockPi;

	beforeEach(() => {
		vi.resetModules();
		mockPi = createMockPi();
	});

	// ── Command Registration ──────────────────────────────────────────

	describe("command registration", () => {
		it("should export a default function", async () => {
			const mod = await loadExtension();
			expect(typeof mod.default).toBe("function");
		});

		it("should register exactly 5 commands", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);
			expect(mockPi.registerCommand).toHaveBeenCalledTimes(5);
		});

		it("each command should have a description and handler", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			for (const cmd of mockPi.registeredCommands) {
				expect(typeof cmd.options.description).toBe("string");
				expect(cmd.options.description.length).toBeGreaterThan(0);
				expect(typeof cmd.options.handler).toBe("function");
			}
		});

		it("should register all expected command names", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const names = mockPi.registeredCommands.map((c) => c.name);
			expect(names).toContain("cli-anything");
			expect(names).toContain("cli-anything:refine");
			expect(names).toContain("cli-anything:test");
			expect(names).toContain("cli-anything:validate");
			expect(names).toContain("cli-anything:list");
		});
	});

	// ── /cli-anything Command ─────────────────────────────────────────

	describe("/cli-anything command", () => {
		it("should send user message with HARNESS.md, command spec, and user args", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything",
			);
			expect(cmd).toBeDefined();

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler(" /path/to/software", mockCtx);

			expect(mockPi.sendUserMessage).toHaveBeenCalledTimes(1);
			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("[CLI-Anything Command: cli-anything]");
			expect(msg).toContain(MOCK_HARNESS);
			expect(msg).toContain("# cli-anything command mock");
			expect(msg).toContain("/path/to/software");
			expect(msg).toContain("Extension Asset Paths");
			expect(msg).toContain("Path Remapping Rules");
		});

		it("should show warning when invoked without args", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything",
			);

			const mockNotify = vi.fn();
			const mockCtx: MockContext = { ui: { notify: mockNotify } };
			await cmd!.options.handler("  ", mockCtx);

			expect(mockNotify).toHaveBeenCalledTimes(1);
			expect(mockNotify).toHaveBeenCalledWith(
				expect.stringContaining("Usage: /cli-anything"),
				"warning",
			);
			expect(mockPi.sendUserMessage).not.toHaveBeenCalled();
		});
	});

	// ── /cli-anything:refine Command ──────────────────────────────────

	describe("/cli-anything:refine command", () => {
		it("should send user message with correct context when args provided", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:refine",
			);
			expect(cmd).toBeDefined();

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("/path/to/harness", mockCtx);

			expect(mockPi.sendUserMessage).toHaveBeenCalledTimes(1);
			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("[CLI-Anything Command: cli-anything:refine]");
			expect(msg).toContain(MOCK_HARNESS);
			expect(msg).toContain("# refine command mock");
			expect(msg).toContain("/path/to/harness");
		});

		it("should show warning when invoked without args", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:refine",
			);

			const mockNotify = vi.fn();
			const mockCtx: MockContext = { ui: { notify: mockNotify } };
			await cmd!.options.handler("", mockCtx);

			expect(mockNotify).toHaveBeenCalledTimes(1);
			expect(mockNotify).toHaveBeenCalledWith(
				expect.stringContaining("Usage: /cli-anything:refine"),
				"warning",
			);
			expect(mockPi.sendUserMessage).not.toHaveBeenCalled();
		});
	});

	// ── /cli-anything:test Command ────────────────────────────────────

	describe("/cli-anything:test command", () => {
		it("should send user message with correct context when args provided", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:test",
			);
			expect(cmd).toBeDefined();

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("/path/to/project", mockCtx);

			expect(mockPi.sendUserMessage).toHaveBeenCalledTimes(1);
			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("[CLI-Anything Command: cli-anything:test]");
			expect(msg).toContain(MOCK_HARNESS);
			expect(msg).toContain("# test command mock");
			expect(msg).toContain("/path/to/project");
		});

		it("should show warning when invoked without args", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:test",
			);

			const mockNotify = vi.fn();
			const mockCtx: MockContext = { ui: { notify: mockNotify } };
			await cmd!.options.handler("   ", mockCtx);

			expect(mockNotify).toHaveBeenCalledTimes(1);
			expect(mockNotify).toHaveBeenCalledWith(
				expect.stringContaining("Usage: /cli-anything:test"),
				"warning",
			);
			expect(mockPi.sendUserMessage).not.toHaveBeenCalled();
		});
	});

	// ── /cli-anything:validate Command ────────────────────────────────

	describe("/cli-anything:validate command", () => {
		it("should send user message with correct context when args provided", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:validate",
			);
			expect(cmd).toBeDefined();

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("/repo/url", mockCtx);

			expect(mockPi.sendUserMessage).toHaveBeenCalledTimes(1);
			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("[CLI-Anything Command: cli-anything:validate]");
			expect(msg).toContain(MOCK_HARNESS);
			expect(msg).toContain("# validate command mock");
			expect(msg).toContain("/repo/url");
		});

		it("should show warning when invoked without args", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:validate",
			);

			const mockNotify = vi.fn();
			const mockCtx: MockContext = { ui: { notify: mockNotify } };
			await cmd!.options.handler("", mockCtx);

			expect(mockNotify).toHaveBeenCalledTimes(1);
			expect(mockNotify).toHaveBeenCalledWith(
				expect.stringContaining("Usage: /cli-anything:validate"),
				"warning",
			);
			expect(mockPi.sendUserMessage).not.toHaveBeenCalled();
		});
	});

	// ── /cli-anything:list Command ────────────────────────────────────

	describe("/cli-anything:list command", () => {
		it("should work with no arguments", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:list",
			);

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("", mockCtx);

			expect(mockPi.sendUserMessage).toHaveBeenCalledTimes(1);
			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("[CLI-Anything Command: cli-anything:list]");
			expect(msg).toContain("(no arguments");
		});

		it("should pass flags through", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:list",
			);

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("--json --depth 2", mockCtx);

			expect(mockPi.sendUserMessage).toHaveBeenCalledTimes(1);
			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("--json --depth 2");
		});

		it("getArgumentCompletions should return matching flags", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:list",
			);

			const completions = cmd!.options.getArgumentCompletions!("--j");
			expect(completions).toEqual([{ value: "--json", label: "--json" }]);
		});

		it("getArgumentCompletions should return null for unknown prefix", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:list",
			);

			const completions = cmd!.options.getArgumentCompletions!("--unknown");
			expect(completions).toBeNull();
		});
	});

	// ── Error Handling ────────────────────────────────────────────────

	describe("error handling", () => {
		it("mocked readFileSync throws for unknown paths", async () => {
			// readAsset is a private function (not exported from index.ts),
			// so we verify the contract through the mocked readFileSync:
			// - Known assets resolve correctly
			// - Unknown paths throw with ENOENT
			const { readFileSync } = await import("node:fs");

			// Known asset resolves
			expect(typeof readFileSync("some/HARNESS.md", "utf-8")).toBe("string");

			// Known command resolves
			expect(typeof readFileSync(join("commands", "refine.md"), "utf-8")).toBe("string");

			// Unknown path throws
			expect(() => readFileSync("/nonexistent/file.md", "utf-8")).toThrow(
				/ENOENT/,
			);
		});
	});
});
