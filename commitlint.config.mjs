export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "scope-enum": [
      2,
      "always",
      [
        "domain",
        "db",
        "ingest",
        "kb",
        "tutor",
        "assess",
        "learner",
        "llm",
        "eval",
        "api",
        "web",
        "ci",
        "deploy",
        "docs",
        "repo",
        "scripts",
        "project",
        "decisions",
      ],
    ],
  },
};
