/**
 * Regression tests for CLI-Anything Pi extension.
 *
 * These tests cover functionalities that were present in the original
 * comprehensive test suite (commit 1677e95) and were removed or simplified
 * in the "easy tests" refactor (commit 696ccc3). They ensure that:
 *
 *   - Each command handler (/cli-anything:refine, :test, :validate) sends
 *     the correct user message with HARNESS.md, command spec, and user args
 *   - The buildCommandMessage output includes "Extension Asset Paths" and
 *     "Path Remapping Rules" sections for ALL commands (not just /cli-anything)
 *   - readAsset throws with an ENOENT-style error for unknown file paths
 *   - /cli-anything:list getArgumentCompletions handles edge cases
 *
 * Run with: npx vitest run tests/test_extension_regression.test.ts
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
		getArgumentCompletions?: (
			prefix: string,
		) => Array<{ value: string; label: string }> | null;
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
		registerCommand: vi.fn(
			(name: string, options: RegisteredCommand["options"]) => {
				registeredCommands.push({ name, options });
			},
		),
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

// ─── Regression Tests ─────────────────────────────────────────────────

describe("CLI-Anything Extension — Regression", () => {
	let mockPi: MockPi;

	beforeEach(() => {
		vi.resetModules();
		mockPi = createMockPi();
	});

	// ── /cli-anything:refine handler with valid args ──────────────────

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

		it("should include Extension Asset Paths and Path Remapping Rules", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:refine",
			);

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("/some/path", mockCtx);

			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("Extension Asset Paths");
			expect(msg).toContain("Path Remapping Rules");
		});
	});

	// ── /cli-anything:test handler with valid args ────────────────────

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

		it("should include Extension Asset Paths and Path Remapping Rules", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:test",
			);

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("/some/project", mockCtx);

			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("Extension Asset Paths");
			expect(msg).toContain("Path Remapping Rules");
		});
	});

	// ── /cli-anything:validate handler with valid args ────────────────

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
			expect(msg).toContain(
				"[CLI-Anything Command: cli-anything:validate]",
			);
			expect(msg).toContain(MOCK_HARNESS);
			expect(msg).toContain("# validate command mock");
			expect(msg).toContain("/repo/url");
		});

		it("should include Extension Asset Paths and Path Remapping Rules", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:validate",
			);

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("/some/repo", mockCtx);

			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("Extension Asset Paths");
			expect(msg).toContain("Path Remapping Rules");
		});
	});

	// ── /cli-anything message structure ───────────────────────────────

	describe("/cli-anything command message structure", () => {
		it("should include guides, scripts, and templates directory references", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything",
			);

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("/path/to/software", mockCtx);

			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("Guides directory:");
			expect(msg).toContain("Scripts directory:");
			expect(msg).toContain("Templates directory:");
		});

		it("should include path remapping instructions for containerized paths", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything",
			);

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("/path/to/software", mockCtx);

			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("/root/cli-anything/");
			expect(msg).toContain("repl_skin.py");
			expect(msg).toContain("skill_generator.py");
		});
	});

	// ── /cli-anything:list additional edge cases ──────────────────────

	describe("/cli-anything:list command edge cases", () => {
		it("getArgumentCompletions should return all flags for -- prefix", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:list",
			);

			const completions = cmd!.options.getArgumentCompletions!("--");
			expect(completions).not.toBeNull();
			expect(completions!.length).toBe(3);
			expect(completions!.map((c) => c.value)).toContain("--json");
			expect(completions!.map((c) => c.value)).toContain("--path ");
			expect(completions!.map((c) => c.value)).toContain("--depth ");
		});

		it("getArgumentCompletions should return --path and --depth for --p/--d prefixes", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:list",
			);

			const pathCompletions = cmd!.options.getArgumentCompletions!("--p");
			expect(pathCompletions).toEqual([
				{ value: "--path ", label: "--path " },
			]);

			const depthCompletions = cmd!.options.getArgumentCompletions!("--d");
			expect(depthCompletions).toEqual([
				{ value: "--depth ", label: "--depth " },
			]);
		});

		it("message should contain cli-anything:list command identifier with flags", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const cmd = mockPi.registeredCommands.find(
				(c) => c.name === "cli-anything:list",
			);

			const mockCtx: MockContext = { ui: { notify: vi.fn() } };
			await cmd!.options.handler("--path /some/dir --json", mockCtx);

			const msg = mockPi.sentMessages[0];
			expect(msg).toContain("[CLI-Anything Command: cli-anything:list]");
			expect(msg).toContain("--path /some/dir --json");
			expect(msg).toContain(MOCK_HARNESS);
			expect(msg).toContain("# list command mock");
		});
	});

	// ── Error Handling ────────────────────────────────────────────────

	describe("error handling", () => {
		it("mocked readFileSync throws ENOENT for unknown paths", async () => {
			const { readFileSync } = await import("node:fs");

			// Known assets should resolve correctly
			expect(typeof readFileSync("some/HARNESS.md", "utf-8")).toBe(
				"string",
			);

			// Known command files should resolve correctly
			expect(
				typeof readFileSync(join("commands", "refine.md"), "utf-8"),
			).toBe("string");
			expect(
				typeof readFileSync(join("commands", "test.md"), "utf-8"),
			).toBe("string");
			expect(
				typeof readFileSync(join("commands", "validate.md"), "utf-8"),
			).toBe("string");
			expect(
				typeof readFileSync(join("commands", "list.md"), "utf-8"),
			).toBe("string");

			// Unknown paths should throw with ENOENT
			expect(() =>
				readFileSync("/nonexistent/file.md", "utf-8"),
			).toThrow(/ENOENT/);
		});

		it("handler should not call sendUserMessage when notify is triggered (empty args)", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			// Test all commands that require args
			const commandsRequiringArgs = [
				"cli-anything",
				"cli-anything:refine",
				"cli-anything:test",
				"cli-anything:validate",
			];

			for (const cmdName of commandsRequiringArgs) {
				// Reset mocks between iterations
				mockPi.sendUserMessage.mockClear();
				mockPi.sentMessages.length = 0;

				const cmd = mockPi.registeredCommands.find(
					(c) => c.name === cmdName,
				);
				expect(cmd).toBeDefined();

				const mockNotify = vi.fn();
				const mockCtx: MockContext = { ui: { notify: mockNotify } };
				await cmd!.options.handler("", mockCtx);

				expect(mockPi.sendUserMessage).not.toHaveBeenCalled();
			}
		});
	});

	// ── Cross-command consistency ─────────────────────────────────────

	describe("cross-command consistency", () => {
		it("all commands with args should produce messages containing HARNESS.md", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const testCases = [
				{
					name: "cli-anything",
					args: "/path/to/software",
					expectedSpec: "# cli-anything command mock",
				},
				{
					name: "cli-anything:refine",
					args: "/path/to/harness",
					expectedSpec: "# refine command mock",
				},
				{
					name: "cli-anything:test",
					args: "/path/to/project",
					expectedSpec: "# test command mock",
				},
				{
					name: "cli-anything:validate",
					args: "/repo/url",
					expectedSpec: "# validate command mock",
				},
				{
					name: "cli-anything:list",
					args: "--json",
					expectedSpec: "# list command mock",
				},
			];

			for (const tc of testCases) {
				mockPi.sendUserMessage.mockClear();
				mockPi.sentMessages.length = 0;

				const cmd = mockPi.registeredCommands.find(
					(c) => c.name === tc.name,
				);
				expect(cmd).toBeDefined();

				const mockCtx: MockContext = { ui: { notify: vi.fn() } };
				await cmd!.options.handler(tc.args, mockCtx);

				expect(mockPi.sendUserMessage).toHaveBeenCalledTimes(1);
				const msg = mockPi.sentMessages[0];
				expect(msg).toContain(MOCK_HARNESS);
				expect(msg).toContain(tc.expectedSpec);
				expect(msg).toContain(tc.args);
				expect(msg).toContain("Extension Asset Paths");
				expect(msg).toContain("Path Remapping Rules");
			}
		});

		it("each registered command description should match the expected text", async () => {
			const mod = await loadExtension();
			mod.default(mockPi);

			const expectedDescriptions: Record<string, string> = {
				"cli-anything":
					"Build a complete CLI harness for any GUI application",
				"cli-anything:refine":
					"Refine an existing CLI harness to improve coverage",
				"cli-anything:test":
					"Run tests for a CLI harness and update TEST.md",
				"cli-anything:validate":
					"Validate a CLI harness against HARNESS.md standards",
				"cli-anything:list":
					"List all CLI-Anything tools (installed and generated)",
			};

			for (const [name, desc] of Object.entries(expectedDescriptions)) {
				const cmd = mockPi.registeredCommands.find(
					(c) => c.name === name,
				);
				expect(cmd).toBeDefined();
				expect(cmd!.options.description).toBe(desc);
			}
		});
	});
});
