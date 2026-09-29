// Same config as the TS project, minus `defineConfig` (an identity helper): this repo has no
// node_modules — Allure 3 runs via `npx allure@3.14.3` only as the HTML generator.
export default {
  name: 'Juice Shop E2E',
  output: 'allure-report',
  // Persisted (and cached in CI) so the report keeps its trend and flaky
  // history across runs.
  historyPath: 'allure-history/history.jsonl',
  plugins: {
    awesome: {
      options: {
        reportName: 'Juice Shop E2E',
        groupBy: ['epic', 'category'],
      },
    },
  },
};
