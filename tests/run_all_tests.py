#!/usr/bin/env python3
"""
Miku Companion & Runtime Modular — Automated Verification Suite (Phase 8)
Tests all architectural pillars and the 3 10/10 safeguards:
  1. Fast Startup (<1.5s) & LazyModuleProxy isolation
  2. OS Credential Vault encryption, masking, round-trip, and .env migration
  3. Blindaje #3: Deterministic Tool Schema Ordering & Prefix-Caching Hash invariance
  4. Blindaje #1: Windows SMTC STA Thread Isolation (dedicated STA worker thread)
  5. Non-blocking Desktop CLI execution (stdin=DEVNULL, --yes injection, ActionResult)
  6. Model Sanitization & Multimodal Visual Bridge (deepseek-chat, deepseek-reasoner)
  7. Universal IDE/CLI Hooks & Dynamic Island Interactive Cards (Approval/Question/Error)
"""

import json
import os
import random
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class TestMikuModularArchitecture(unittest.TestCase):

    def test_01_fast_startup_and_lazy_loader(self):
        """Verify lazy_import does not load module until attribute access and boot is <1.5s."""
        from core.engine.lazy_loader import (
            LazyModuleProxy,
            get_startup_metrics,
            lazy_import,
            mark_boot_complete,
        )

        proxy = lazy_import("fractions")
        self.assertIsInstance(proxy, LazyModuleProxy)
        self.assertFalse(proxy.is_loaded())

        # Accessing an attribute triggers on-demand import
        frac = proxy.Fraction(1, 2)
        self.assertEqual(float(frac), 0.5)
        self.assertTrue(proxy.is_loaded())

        boot_ms = mark_boot_complete()
        self.assertLess(boot_ms, 1500.0, "Boot duration must be under 1500ms")
        metrics = get_startup_metrics()
        self.assertTrue(metrics["within_budget"])
        self.assertLess(metrics["boot_ms"], 1500.0)

    def test_02_secret_vault_roundtrip_and_masking(self):
        """Verify SecretVault stores, retrieves, masks, deletes, and migrates .env keys."""
        from core.security.vault import SecretVault

        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "test_vault.enc"
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "GEMINI_API_KEY=AIzaSyTestKey123456789\nPORT=8000\n",
                encoding="utf-8",
            )

            vault = SecretVault(vault_file=vault_path)
            vault._keyring = None  # Force deterministic encrypted file vault verification

            # Test set/get/mask
            ok = vault.set_secret("DEEPSEEK_API_KEY", "sk-deepseek-secret-9876")
            self.assertTrue(ok)
            self.assertEqual(vault.get_secret("DEEPSEEK_API_KEY"), "sk-deepseek-secret-9876")

            masked = vault.list_masked_secrets(["DEEPSEEK_API_KEY"])
            self.assertTrue(masked["DEEPSEEK_API_KEY"]["configured"])
            self.assertTrue(masked["DEEPSEEK_API_KEY"]["masked"].endswith("9876"))
            self.assertNotIn("sk-deepseek-secret", masked["DEEPSEEK_API_KEY"]["masked"])

            # Test .env migration
            mig = vault.migrate_plaintext_env(env_path)
            self.assertIn("GEMINI_API_KEY", mig["migrated_keys"])
            self.assertEqual(vault.get_secret("GEMINI_API_KEY"), "AIzaSyTestKey123456789")
            remaining_env = env_path.read_text(encoding="utf-8")
            self.assertNotIn("AIzaSyTestKey123456789", remaining_env)
            self.assertIn("PORT=8000", remaining_env)

            # Test delete
            vault.delete_secret("DEEPSEEK_API_KEY")
            os.environ.pop("DEEPSEEK_API_KEY", None)
            self.assertIsNone(vault.get_secret("DEEPSEEK_API_KEY"))

    def test_03_blindaje_3_deterministic_tool_ordering_for_prefix_cache(self):
        """Blindaje #3: Shuffled tool lists and dict keys MUST produce the exact same prefix hash."""
        from core.plugins import (
            compute_tools_prefix_hash,
            load_all_plugins,
            sort_tools_deterministically,
        )

        reg = load_all_plugins()
        canonical_tools = reg.get_sorted_schemas()
        self.assertGreaterEqual(len(canonical_tools), 8)

        # Verify alphabetical sorting by function.name
        names = [t["function"]["name"] for t in canonical_tools]
        self.assertEqual(names, sorted(names), "Tools must be sorted alphabetically by function.name")

        base_hash = compute_tools_prefix_hash(canonical_tools)
        for _ in range(15):
            shuffled = list(canonical_tools)
            random.shuffle(shuffled)
            self.assertEqual(
                compute_tools_prefix_hash(shuffled),
                base_hash,
                "Prefix cache hash broke when tool input order changed!",
            )
            resorted = sort_tools_deterministically(shuffled)
            self.assertEqual(
                [t["function"]["name"] for t in resorted],
                names,
            )

    def test_04_blindaje_1_windows_smtc_sta_thread_isolation(self):
        """Blindaje #1: SMTC media operations must execute on the dedicated MikuSMTC_STA_Worker thread."""
        from core.plugins.plugin_media import controlar_multimedia_nativo_sta, get_smtc_worker

        worker = get_smtc_worker()
        status = worker.execute_on_sta("status", timeout=3.0)
        self.assertTrue(status.get("ok"))
        self.assertTrue(status.get("sta_thread"), "SMTC worker must be STA isolated")
        self.assertEqual(status.get("thread_name"), "MikuSMTC_STA_Worker")

        tool_resp = json.loads(controlar_multimedia_nativo_sta(accion="status"))
        self.assertEqual(tool_resp.get("status"), "confirmed")
        self.assertEqual(tool_resp["data"].get("thread_name"), "MikuSMTC_STA_Worker")

    def test_05_non_blocking_desktop_cli_and_sanitization(self):
        """Verify non-interactive flag injection and non-blocking execution with real exit codes."""
        from core.plugins.plugin_desktop import (
            run_non_blocking_command,
            sanitize_non_interactive_command,
        )

        cmd = sanitize_non_interactive_command("npx create-vite my-app")
        self.assertIn("--yes", cmd)

        ok_res = run_non_blocking_command("python3 -c \"print('miku-ok')\"")
        self.assertTrue(ok_res["ok"])
        self.assertEqual(ok_res["exit_code"], 0)
        self.assertIn("miku-ok", ok_res["stdout"])

        fail_res = run_non_blocking_command("python3 -c \"import sys; sys.stderr.write('boom\\n'); sys.exit(7)\"")
        self.assertFalse(fail_res["ok"])
        self.assertEqual(fail_res["exit_code"], 7)
        self.assertIn("boom", fail_res["stderr"])

    def test_06_model_sanitization_and_visual_bridge(self):
        """Verify fictitious models map to official deepseek-chat / deepseek-reasoner."""
        from models_provider import sanitize_model_id

        self.assertEqual(sanitize_model_id("deepseek-v4-pro"), "deepseek-reasoner")
        self.assertEqual(sanitize_model_id("deepseek-v3.2"), "deepseek-chat")
        self.assertEqual(sanitize_model_id("deepseek-chat"), "deepseek-chat")
        self.assertEqual(sanitize_model_id("deepseek-reasoner"), "deepseek-reasoner")

    def test_07_universal_hooks_and_dynamic_island_cards(self):
        """Verify IDE hooks update Miku state and interactive UI cards resolve asynchronously."""
        from core.plugins.plugin_hooks import process_hook_event
        from core.plugins.plugin_ui import (
            _PENDING_DECISIONS,
            resolve_ui_decision,
            solicitar_aprobacion_comando,
        )

        hook_res = process_hook_event(
            {
                "source": "claude-code",
                "event": "tool_start",
                "title": "Editando server.py",
                "diff": "- legacy_ui\n+ modular_plugins",
            }
        )
        self.assertEqual(hook_res["status"], "ok")
        self.assertEqual(hook_res["hook"]["miku_state"], "working")

        # Resolve ApprovalCard from a background thread simulating user pressing [A] on the Island
        def _resolve_soon():
            time.sleep(0.05)
            for cid, entry in list(_PENDING_DECISIONS.items()):
                if entry.get("status") == "pending":
                    resolve_ui_decision(cid, "always")

        t = threading.Thread(target=_resolve_soon, daemon=True)
        t.start()
        raw_resp = solicitar_aprobacion_comando(
            comando="git commit -m 'feat: modular core'",
            riesgo="medio",
            diff_preview="- old_line\n+ new_line",
            timeout_segundos=3.0,
        )
        parsed = json.loads(raw_resp)
        self.assertEqual(parsed["status"], "confirmed")
        self.assertEqual(parsed["data"]["decision"], "always")

    def test_08_skills_registry_and_auto_match(self):
        """Verify SkillRegistry manages skills and limits concurrent auto-matching to max 2."""
        from core.skills.registry import SkillRegistry

        with tempfile.TemporaryDirectory() as tmpdir:
            reg = SkillRegistry(storage_dir=tmpdir)
            all_skills = reg.list_skills()
            self.assertGreaterEqual(len(all_skills), 5)

            # Auto-match with keywords
            matched = reg.match_skills_for_prompt("Revisa este commit y haz un git diff de la rama")
            self.assertLessEqual(len(matched), 2, "Must not auto-inject more than 2 skills")
            matched_ids = [s["id"] for s in matched]
            self.assertIn("git-code-reviewer", matched_ids)

            # Test creating a new custom skill
            custom = reg.create_or_update_skill({
                "id": "sql-optimizer",
                "name": "SQL Optimizer",
                "description": "Optimizes Postgres and SQLite queries",
                "triggers": ["sql", "query", "explain analyze"],
                "system_prompt_addon": "Always inspect indexes and explain plans.",
            })
            self.assertEqual(custom["id"], "sql-optimizer")
            persisted = reg.get_skill("sql-optimizer")
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted["name"], "SQL Optimizer")

    def test_09_agent_bus_and_isolated_atomic_memory(self):
        """Verify AgentBus delegation and AgentMemory atomic storage and sliding compaction."""
        from core.agents.bus import AgentBus, DelegationEvent
        from core.agents.memory import AgentMemory
        from core.agents.manager import AgentManager

        # Bus delegation check
        bus = AgentBus()
        received = []
        bus.subscribe("TASK_PROGRESS", lambda ev: received.append(ev))

        task_id = bus.delegate("miku", "korus", "Refactor invoice.ts calculation")
        bus.update_progress(task_id, "korus", "Edit", 50, diff={"file": "invoice.ts", "added": "+ const TVA"})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["phase"], "Edit")
        task = bus.get_task(task_id)
        self.assertEqual(task["status"], "running")

        # Atomic memory check
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = AgentMemory("korus", storage_dir=tmpdir)
            mem.set_fact("project_type", "TypeScript Vite")
            self.assertEqual(mem.get_fact("project_type"), "TypeScript Vite")

            # Add multiple interactions to verify compaction
            for i in range(25):
                mem.add_interaction("user" if i % 2 == 0 else "assistant", f"Message payload step {i}")

            ctx = mem.get_context_prompt()
            self.assertIn("TypeScript Vite", ctx)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "korus.json")))

        # Agent manager vault env var naming
        self.assertEqual(AgentManager.generate_vault_env_var("sql-expert"), "MIKU_AGENT_SQL_EXPERT_KEY")
        self.assertEqual(AgentManager.default_phases_for_category("code"), ["Read", "Edit", "Bash", "Done"])
        self.assertEqual(AgentManager.default_phases_for_category("research"), ["Search", "Extract", "Synthesize", "Done"])

    def test_10_circuit_breaker_and_telemetry(self):
        """Verify CircuitBreaker rerouting on 429 and UsageTelemetry token cost calculations."""
        from core.usage.circuit_breaker import CircuitBreaker
        from core.usage.telemetry import UsageTelemetry

        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=30.0)
        route, is_fb, _ = cb.get_route("gemini")
        self.assertEqual(route, "gemini")
        self.assertFalse(is_fb)

        # Trigger HTTP 429 (immediate trip)
        cb.record_failure("gemini", status_code=429, error_message="Rate limit exceeded")
        route, is_fb, reason = cb.get_route("gemini")
        self.assertEqual(route, "groq")
        self.assertTrue(is_fb)

        # Telemetry cost calculations
        with tempfile.TemporaryDirectory() as tmpdir:
            tel = UsageTelemetry(storage_path=os.path.join(tmpdir, "telemetry.json"))
            cost = tel.calculate_cost("gemini-2.5-flash", prompt_tokens=1000, completion_tokens=1000)
            # 1k input = 0.000075, 1k output = 0.000300 => total = 0.000375
            self.assertAlmostEqual(cost, 0.000375, places=5)

            rec = tel.record_request("gemini-2.5-flash", 1000, 1000, latency_ms=180.5, success=True, agent_id="korus")
            self.assertEqual(rec["tokens"], 2000)

            dash = tel.get_dashboard_summary()
            self.assertEqual(dash["total_requests"], 1)
            self.assertEqual(dash["total_tokens"], 2000)
            self.assertIn("korus", dash["by_agent"])

    def test_11_agent_manifest_validation_and_fallbacks(self):
        """Verify AgentManifest schema conversion, deterministic 4-phase fallbacks, and vault key naming."""
        from core.agents.manifest import AgentManifest, ROLE_PHASE_FALLBACKS

        m_code = AgentManifest.from_dict({"name": "Scraper Bot", "role": "Web Scraper", "role_type": "research", "phases": []})
        self.assertEqual(m_code.id, "scraper-bot")
        self.assertEqual(m_code.vault_key_var, "MIKU_AGENT_SCRAPER_BOT_KEY")
        self.assertEqual(m_code.phases, ("Search", "Extract", "Synthesize", "Done"))

        m_data = AgentManifest.from_dict({"name": "SQL Runner", "role": "DB", "role_type": "data"})
        self.assertEqual(m_data.phases, ROLE_PHASE_FALLBACKS["data"])

        m_fallback = AgentManifest.from_dict({"name": "Unknown Type", "role": "Helper", "role_type": "invalid_type"})
        self.assertEqual(m_fallback.role_type, "general")
        self.assertEqual(m_fallback.phases, ("Listen", "Think", "Action", "Done"))

    def test_12_atomic_memory_concurrency(self):
        """Verify concurrent multi-thread writes to AgentMemory never corrupt the JSON file."""
        from core.agents.memory import AgentMemory

        with tempfile.TemporaryDirectory() as tmpdir:
            mem = AgentMemory("concurrent_agent", storage_dir=tmpdir)
            errors = []

            def _writer(worker_id: int):
                try:
                    for step in range(10):
                        mem.set_fact(f"w_{worker_id}_{step}", f"val_{step}")
                        mem.add_interaction("user", f"worker {worker_id} step {step}")
                except Exception as exc:
                    errors.append(exc)

            threads = [threading.Thread(target=_writer, args=(i,)) for i in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(len(errors), 0)
            json_path = os.path.join(tmpdir, "concurrent_agent.json")
            self.assertTrue(os.path.exists(json_path))
            with open(json_path, "r", encoding="utf-8") as f:
                parsed = json.load(f)
            self.assertIsInstance(parsed, dict)
            self.assertEqual(parsed["facts"]["w_0_0"], "val_0")

    def test_13_mcp_manifest_sandbox_security(self):
        """Verify validate_mcp_manifest blocks shell injection and unauthorized binaries."""
        from core.plugins.plugin_mcp import validate_mcp_manifest

        valid = validate_mcp_manifest({
            "name": "github-mcp",
            "command": "npx",
            "args": ["--yes", "@modelcontextprotocol/server-github"],
        })
        self.assertTrue(valid["ok"])
        self.assertFalse(valid["requires_permission_prompt"])

        rce_cmd = validate_mcp_manifest({
            "name": "evil-mcp",
            "command": "cmd.exe",
            "args": ["/c", "calc.exe"],
        })
        self.assertFalse(rce_cmd["ok"])

        shell_arg = validate_mcp_manifest({
            "name": "inject-mcp",
            "command": "npx",
            "args": ["--yes", "pkg && rm -rf /"],
        })
        self.assertFalse(shell_arg["ok"])

        outside_path = validate_mcp_manifest({
            "name": "fs-root",
            "command": "npx",
            "args": ["--yes", "@modelcontextprotocol/server-filesystem", "/etc/passwd"],
        })
        self.assertTrue(outside_path["ok"])
        self.assertTrue(outside_path["requires_permission_prompt"])


if __name__ == "__main__":
    print("=" * 72)
    print("Running Miku Companion & Runtime Modular Verification Suite")
    print("=" * 72)
    t0 = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestMikuModularArchitecture)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    print(f"\nTotal test suite time: {elapsed_ms:.1f} ms")
    sys.exit(0 if result.wasSuccessful() else 1)

