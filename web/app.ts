export type PromptEntry = {
  id: string;
  name: string;
  content: string;
  template?: string;
  updated_at?: string;
};

export type TemplateEntry = {
  id: string;
  name: string;
  body: string;
};

export type PresetEntry = {
  id: string;
  name: string;
  prompt: string;
};

export type PromptCatalog = {
  presets: PresetEntry[];
  templates: TemplateEntry[];
  prompts: PromptEntry[];
  settings: { theme: string; autosave: boolean };
};

export const defaultCatalog: PromptCatalog = {
  presets: [
    {
      id: "neon-research",
      name: "Neon Research",
      prompt:
        "Gather primary facts, sources, and citations. Return bulletproof notes with links and dates.",
    },
    {
      id: "stealth-coder",
      name: "Stealth Coder",
      prompt:
        "Produce minimal, secure code with inline rationale. Prefer small diffs and explicit tests.",
    },
    {
      id: "critic-loop",
      name: "Critic Loop",
      prompt:
        "Review output for safety, bias, and correctness. Suggest concrete fixes and retry plan.",
    },
  ],
  templates: [
    {
      id: "mission-brief",
      name: "Mission Brief",
      body:
        "## Objective\n{objective}\n\n## Constraints\n{constraints}\n\n## Plan\n- {steps}\n\n## Deliverables\n- {deliverables}",
    },
    {
      id: "code-task",
      name: "Code Task",
      body:
        "Context:\n{context}\n\nAcceptance criteria:\n{criteria}\n\nTest plan:\n{tests}",
    },
    {
      id: "retro",
      name: "Retro",
      body:
        "What went well:\n{positive}\n\nWhat broke:\n{issues}\n\nNext iteration:\n{actions}",
    },
  ],
  prompts: [],
  settings: { theme: "cyberpunk", autosave: true },
};

export function mergeCatalog(
  base: PromptCatalog,
  override?: Partial<PromptCatalog>,
): PromptCatalog {
  return {
    presets: override?.presets ?? base.presets,
    templates: override?.templates ?? base.templates,
    prompts: override?.prompts ?? base.prompts,
    settings: override?.settings ?? base.settings,
  };
}
