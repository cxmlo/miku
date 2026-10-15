# Proactive Planning and Clarification Rule

Whenever the user requests a new feature, architecture change, or complex implementation plan, you (the agent) MUST follow this rule BEFORE executing code:

1. **Ask Clarifying Questions:** Do not assume implementation details if they are ambiguous. Proactively ask the user how they envision the UI, what their preferred behavior is, and how edge cases should be handled.
2. **Present Options:** If there are multiple ways to implement a feature (e.g., using a Bottom Sheet vs a Modal in React Native, or saving to AsyncStorage vs SQLite), briefly present the options and ask the user which one they prefer.
3. **Include Questions in the Plan:** When generating the `implementation_plan.md` artifact, always include a section titled "Open Questions" or "User Review Required" highlighting the design decisions that need their input.
4. **Don't Rush Execution:** Wait for the user to answer these questions and explicitly approve the plan before starting to write or modify code. 

Your goal is to ensure the final implementation perfectly aligns with the user's vision and avoids rework.
