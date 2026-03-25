import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { type AgentMessage } from "@mariozechner/pi-agent-core";
import * as fs from "fs";
import * as path from "path";

/**
 * Ouroboros V2 Extension - Recursive Self-Prompting AI
 *
 * Integrates Ouroboros self-improvement logic directly into the Pi coding agent.
 */

interface OuroborosState {
    active: boolean;
    iterations: number;
    maxIterations: number;
    currentFocus: string;
    currentMilestone: string;
    insights: string[];
    restPeriodMs: number;
}

export default function (pi: ExtensionAPI) {
    const stateFile = path.join(".ouroboros", "v2_state.json");
    let state: OuroborosState = {
        active: false,
        iterations: 0,
        maxIterations: 15,
        currentFocus: "Initialize system",
        currentMilestone: "Phase 1: Capacity Optimization",
        insights: [],
        restPeriodMs: 15000, // 15s rest to avoid 429s
    };

    // Load state if exists
    if (fs.existsSync(stateFile)) {
        try {
            state = JSON.parse(fs.readFileSync(stateFile, "utf-8"));
        } catch (e) {
            console.error("Failed to load Ouroboros state", e);
        }
    }

    const saveState = () => {
        const dir = path.dirname(stateFile);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
    };

    // Convergence tracking - measures if insights are stabilizing
    const calculateConvergence = (): number => {
        if (state.insights.length < 2) return 0;
        // Simple convergence: are insights repeating/stabilizing?
        const recent = state.insights.slice(-5);
        const unique = new Set(recent).size;
        return Math.round((1 - unique / recent.length) * 100);
    };

    // Update TUI status line
    const updateTui = (ctx: any) => {
        const status = state.active ? "Loop: ACTIVE" : "Loop: IDLE";
        const info = `${status} | Iter: ${state.iterations}/${state.maxIterations} | Phase: ${state.currentMilestone}`;
        ctx.ui.setStatus("ouroboros", info);

        // Add iteration metrics widget
        if (state.active) {
            ctx.ui.setWidget("ouroboros-metrics", {
                type: "panel",
                title: "Ouroboros Metrics",
                rows: [
                    `Iteration: ${state.iterations}/${state.maxIterations}`,
                    `Focus: ${state.currentFocus}`,
                    `Insights: ${state.insights.length}`,
                    `Phase: ${state.currentMilestone}`,
                ],
            });
        } else {
            ctx.ui.setWidget("ouroboros-metrics", null);
        }
    };

    // Combined TUI update with convergence indicator
    const updateTuiWithConvergence = (ctx: any) => {
        updateTui(ctx);
        if (state.active && state.iterations > 2) {
            const convergence = calculateConvergence();
            ctx.ui.setWidget("ouroboros-convergence", {
                type: "progress",
                title: "Convergence",
                value: convergence,
                max: 100,
            });
        } else {
            ctx.ui.setWidget("ouroboros-convergence", null);
        }
    };

    // Register command
    pi.registerCommand("ouroboros", {
        description: "Manage Ouroboros self-prompting loop",
        handler: async (args, ctx) => {
            const parts = args.trim().split(/\s+/);
            const cmd = parts[0];

            if (cmd === "start") {
                state.active = true;
                state.maxIterations = parseInt(parts[1]) || 15;
                saveState();
                updateTuiWithConvergence(ctx);
                ctx.ui.notify(`Ouroboros loop started (max ${state.maxIterations} iterations)`, "info");
                
                if (ctx.isIdle()) {
                    triggerNextPrompt(ctx);
                }
            } else if (cmd === "stop") {
                state.active = false;
                saveState();
                updateTuiWithConvergence(ctx);
                ctx.ui.notify("Ouroboros loop stopped", "info");
            } else if (cmd === "status") {
                await updateRoadmapStatus(ctx);
                ctx.ui.notify(`Ouroboros: ${state.active ? "ACTIVE" : "INACTIVE"}, Phase: ${state.currentMilestone}, Focus: ${state.currentFocus}`, "info");
            } else if (cmd === "meta") {
                await updateMetaPrompts(ctx);
            } else if (cmd === "health") {
                await runHealthCheck(ctx);
            } else if (cmd === "rollback") {
                await triggerRollback(ctx);
            } else if (cmd === "experiment") {
                const script = parts[1] || "train.py";
                await runExperiment(script, ctx);
            } else {
                ctx.ui.notify("Usage: /ouroboros <start [n]|stop|status|meta|health|rollback|experiment [script]>", "warning");
            }
        },
    });

    // Roadmap Integration
    async function updateRoadmapStatus(ctx: any): Promise<any> {
        try {
            const result = await pi.exec("bash", ["-c", "export PYTHONPATH=. && python3 src/ouroboros/v2/roadmap_manager.py status"]);
            const roadmap = JSON.parse(result.stdout);
            state.currentMilestone = roadmap.current_milestone;
            saveState();
            updateTuiWithConvergence(ctx);
            return roadmap;
        } catch (e) {
            console.error("Roadmap Error", e);
            return null;
        }
    }

    // Meta-Prompt Engine Integration
    async function updateMetaPrompts(ctx: any) {
        ctx.ui.notify("🧠 Meta-Prompt Engine Analyzing...", "info");
        try {
            const insightsJson = JSON.stringify(state.insights);
            const result = await pi.exec("bash", ["-c", `export PYTHONPATH=. && python3 src/ouroboros/v2/meta_prompter.py update ${JSON.stringify(insightsJson)}`]);
            const updateResult = JSON.parse(result.stdout);

            if (updateResult.new_rules && updateResult.new_rules.length > 0) {
                ctx.ui.notify(`📚 Added ${updateResult.new_rules.length} new prompt rules`, "success");
                pi.appendEntry("system_prompt_update", { content: `\n## Recent Lessons\n${updateResult.new_rules.map((r: any) => `- ${r.content}`).join("\n")}` });
            }
        } catch (e) {
            ctx.ui.notify(`Meta Error: ${e}`, "error");
        }
    }

    // Health Check Integration
    async function runHealthCheck(ctx: any): Promise<boolean> {
        ctx.ui.notify("🏥 Running Health Check...", "info");
        try {
            const result = await pi.exec("bash", ["-c", "export PYTHONPATH=. && python3 src/ouroboros/v2/harness.py check-health"]);
            const health = JSON.parse(result.stdout);

            if (health.status === "healthy" || health.status === "degraded") {
                ctx.ui.notify(`✅ System is ${health.status.toUpperCase()}`, "success");
                return true;
            } else {
                ctx.ui.notify(`🚨 SYSTEM UNHEALTHY: ${health.message}`, "error");
                return false;
            }
        } catch (e) {
            ctx.ui.notify(`Health Check Error: ${e}`, "error");
            return false;
        }
    }

    // Rollback Integration
    async function triggerRollback(ctx: any) {
        ctx.ui.notify("⏳ Triggering Auto-Rollback...", "warning");
        try {
            const result = await pi.exec("bash", ["-c", "export PYTHONPATH=. && python3 src/ouroboros/v2/harness.py rollback"]);
            const rollbackResult = JSON.parse(result.stdout);

            if (rollbackResult.success) {
                ctx.ui.notify(`⏪ ${rollbackResult.message}`, "success");
            } else {
                ctx.ui.notify(`❌ Rollback Failed: ${rollbackResult.message}`, "error");
            }
        } catch (e) {
            ctx.ui.notify(`Rollback Error: ${e}`, "error");
        }
    }

    // Experiment Integration
    async function runExperiment(script: string, ctx: any) {
        ctx.ui.notify(`🔬 Starting Experiment: ${script}...`, "info");
        try {
            const result = await pi.exec("bash", ["-c", `export PYTHONPATH=. && python3 src/ouroboros/v2/harness.py run-experiment ${script} --timeout 600`]);
            const experimentResult = JSON.parse(result.stdout);

            if (experimentResult.success) {
                const bpb = experimentResult.val_bpb;
                ctx.ui.notify(`📈 Experiment Success! val_bpb: ${bpb.toFixed(6)}`, "success");
                state.insights.push(`Experiment with ${script} achieved val_bpb: ${bpb.toFixed(6)}`);
                saveState();
            } else {
                ctx.ui.notify(`❌ Experiment Failed: ${experimentResult.error}`, "error");
            }
        } catch (e) {
            ctx.ui.notify(`Experiment Error: ${e}`, "error");
        }
    }

    // Alignment Firewall Hook
    pi.on("tool_call", async (event, ctx) => {
        if (event.toolName === "write" || event.toolName === "edit") {
            const code = (event.input as any).content || (event.input as any).replace || "";
            if (!code) return;

            ctx.ui.notify("🛡️ Alignment Firewall Validating...", "info");

            try {
                const result = await pi.exec("bash", ["-c", `export PYTHONPATH=. && python3 src/ouroboros/v2/harness.py validate-alignment ${JSON.stringify(code)}`]);
                const decision = JSON.parse(result.stdout);

                if (!decision.approved) {
                    ctx.ui.notify(`🔥 ALIGNMENT FIREWALL BLOCKED: ${decision.summary}`, "error");
                    return { block: true, reason: `Alignment violation: ${decision.summary}` };
                }

                if (decision.halt_required) {
                    ctx.ui.notify("🚨 CRITICAL VIOLATION: SYSTEM HALTED", "error");
                    state.active = false;
                    saveState();
                    return { block: true, reason: "SYSTEM HALTED" };
                }

                ctx.ui.notify("✅ Alignment Approved", "success");
            } catch (e) {
                ctx.ui.notify(`Firewall Error: ${e}`, "error");
                return { block: true, reason: "Firewall execution failed" };
            }
        }
    });

    // Record Modification Hook
    pi.on("tool_result", async (event, ctx) => {
        if (!event.isError && (event.toolName === "write" || event.toolName === "edit")) {
            const files = [(event.input as any).path];
            const diff = event.toolName === "edit" ? (event.input as any).replace : (event.input as any).content;

            try {
                await pi.exec("bash", ["-c", `export PYTHONPATH=. && python3 src/ouroboros/v2/harness.py record-modification -f ${JSON.stringify(files[0])} -d ${JSON.stringify(diff)}`]);
                ctx.ui.notify("📝 Modification Recorded", "info");
            } catch (e) {
                console.error("Failed to record modification", e);
            }
        }
    });

    // Listen for agent completion
    pi.on("agent_end", async (event, ctx) => {
        if (!state.active) return;

        state.iterations++;
        
        const lastMessage = event.messages[event.messages.length - 1];
        if (lastMessage && lastMessage.role === "assistant") {
            const content = lastMessage.content;
            if (typeof content === "string") {
                const insightMatch = content.match(/FOCUS: (.*)/);
                if (insightMatch) {
                    state.insights.push(insightMatch[1]);
                    state.currentFocus = insightMatch[1];
                }
            }
        }
        
        saveState();
        updateTuiWithConvergence(ctx);

        const healthy = await runHealthCheck(ctx);
        if (!healthy) {
            ctx.ui.notify("⚠️ System degradation detected. Pausing loop and rolling back.", "warning");
            state.active = false;
            saveState();
            await triggerRollback(ctx);
            return;
        }

        if (state.iterations >= state.maxIterations) {
            state.active = false;
            saveState();
            ctx.ui.notify("Ouroboros loop completed (reached max iterations)", "info");
            return;
        }

        if (state.iterations % 5 === 0) {
            await updateMetaPrompts(ctx);
        }

        // --- BACKOFF PHASE ---
        ctx.ui.notify(`💤 Rest Phase (${state.restPeriodMs/1000}s) to avoid Rate Limits...`, "info");
        setTimeout(() => {
            if (state.active) triggerNextPrompt(ctx);
        }, state.restPeriodMs);
    });

    pi.on("session_start", async (event, ctx) => {
        updateTuiWithConvergence(ctx);
        await updateRoadmapStatus(ctx);
        
        // Register LM Studio fallback
        pi.registerProvider("lm-studio", {
            baseUrl: "http://localhost:1234/v1",
            apiKey: "not-needed",
            api: "openai-responses",
            models: [{
                id: "local-model",
                name: "LM Studio Local Model",
                reasoning: true,
                input: ["text"],
                cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
                contextWindow: 32768,
                maxTokens: 4096
            }]
        });
    });

    async function triggerNextPrompt(ctx: any) {
        // Read current Roadmap to guide the agent
        const roadmap = await updateRoadmapStatus(ctx);
        const milestone = roadmap ? roadmap.current_milestone : "Unknown";
        const tasks = roadmap ? roadmap.active_tasks.join("\n- ") : "No active tasks";

        ctx.ui.notify(`🔄 Ouroboros Iteration ${state.iterations + 1} Starting...`, "info");
        
        const history = ctx.sessionManager.getBranch();
        const lastMessages = history.slice(-5).filter((m: any) => m.type === "message").map((m: any) => (m as any).message.content);
        
        const reflectionPrompt = `
You are in an Ouroboros Recursive Self-Improvement Loop.
Iteration: ${state.iterations}
Phase: ${milestone}

## Strategic Roadmap
Your current objective is to complete the tasks in: ${milestone}
Active Tasks:
- ${tasks}

## Instructions
1. Reflect on the recent conversation: ${JSON.stringify(lastMessages)}
2. Based on the Roadmap, generate your NEXT prompt to yourself.
3. If you have completed a task, use the command: \`python3 src/ouroboros/v2/roadmap_manager.py complete "task description"\`
4. ALWAYS check your safety protocols (@src/ouroboros/v2/SKILL.md) before any code modification.

Format your response as:
FOCUS: [Short description of next focus]
PROMPT: [The actual prompt you want to execute]
`;

        pi.sendUserMessage(reflectionPrompt);
    }
}
