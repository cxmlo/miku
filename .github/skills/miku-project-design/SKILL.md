---
name: miku-project-design
description: "Use when changing Miku architecture, the Tauri Island, Android Compose UI, visual design, assets, animations, or legacy/frontend boundaries. Follow the repository structure and design system without breaking compatibility."
---

# Miku project architecture and design

Use this skill before adding a feature that crosses desktop, Android, backend, visual design, assets, or animation boundaries.

## Workflow

1. Read `.agent/rules/miku-design-system.md` (`miku-catalogo.html` is the visual source of truth for Configuración and Miku-Link) and `docs/PROJECT_ARCHITECTURE_AND_DESIGN.md` before proposing or editing structure.
2. Identify the owning client and the actual runtime entry point. Tauri packages `miku_ui/src/`; FastAPI still serves `miku_island/` for compatibility.
3. Preserve the current visual identity and use semantic theme tokens instead of scattering new color/style literals.
4. Keep Compose UI, observable screen state, repositories, persistence, and connection lifecycle in separate responsibilities; add abstractions only when they provide a real boundary.
5. Treat asset-pack loading as unimplemented unless a tested loader exists. Never execute code from content packs and always preserve a built-in fallback.
6. Trace consumers before changing an API, event, legacy client, or duplicated asset. Do not remove Expo or fallback files during the mobile migration.
7. Run the focused tests/build for the changed area and update the architecture documentation with the actual result.

## Validation

- Frontend mirror: `python scripts/sync_island.py`
- Update mirror after canonical Tauri frontend edits: `python scripts/sync_island.py --sync`
- Android: from `miku_android/`, run `.\gradlew.bat testDebugUnitTest assembleDebug`
- Backend: run the focused pytest files for the changed contract.

Report any unavailable SDK/toolchain as a validation blocker; do not describe uncompiled code as working.
