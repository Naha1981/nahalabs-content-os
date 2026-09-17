import { defineConfig } from "@trigger.dev/sdk";

export default defineConfig({
  project: "YOUR_TRIGGER_PROJECT_REF",
  dirs: ["./trigger"],
  runtime: "node-22",
  retries: {
    enabledInDev: false,
    default: { maxAttempts: 3, minTimeoutInMs: 1000, maxTimeoutInMs: 10000, factor: 2, randomize: true },
  },
});
