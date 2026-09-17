import { logger, schedules } from "@trigger.dev/sdk";

const API_URL = process.env.REACTIVATE_API_URL;
const API_TOKEN = process.env.REACTIVATE_API_TOKEN;

type Job = {
  id: number;
  name: string;
  job_type: string;
  cron: string;
  timezone: string;
  enabled: boolean;
};

async function runReactivateJob(jobType: string) {
  if (!API_URL) throw new Error("REACTIVATE_API_URL is not configured");

  const jobsResponse = await fetch(`${API_URL}/api/v1/scheduler/jobs`, {
    headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : undefined,
  });
  if (!jobsResponse.ok) throw new Error(`Could not load Reactivate jobs: ${jobsResponse.status}`);

  const data = (await jobsResponse.json()) as { jobs: Job[] };
  const job = data.jobs.find((item) => item.job_type === jobType);
  if (!job) throw new Error(`Reactivate job not found: ${jobType}`);
  if (!job.enabled) return { skipped: true, reason: "disabled", jobType };

  const response = await fetch(`${API_URL}/api/v1/scheduler/jobs/${job.id}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
    },
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || `Reactivate job failed: ${response.status}`);
  logger.info("Reactivate job completed", { jobType, runId: result.run_id });
  return result;
}

export const morningOperator = schedules.task({
  id: "reactivate-morning-operator",
  cron: { pattern: "0 6 * * *", timezone: "Africa/Johannesburg" },
  run: async () => runReactivateJob("MORNING_OPERATOR"),
});

export const radarScan = schedules.task({
  id: "reactivate-radar-scan",
  cron: { pattern: "30 6 * * *", timezone: "Africa/Johannesburg" },
  run: async () => runReactivateJob("RADAR_SCAN"),
});

export const followUpCheck = schedules.task({
  id: "reactivate-follow-up-check",
  cron: { pattern: "0 8,12,16 * * *", timezone: "Africa/Johannesburg" },
  run: async () => runReactivateJob("FOLLOW_UP_CHECK"),
});

export const campaignCheck = schedules.task({
  id: "reactivate-campaign-check",
  cron: { pattern: "0 * * * *", timezone: "Africa/Johannesburg" },
  run: async () => runReactivateJob("CAMPAIGN_CHECK"),
});

export const publishingCheck = schedules.task({
  id: "reactivate-publishing-check",
  cron: { pattern: "*/15 * * * *", timezone: "Africa/Johannesburg" },
  run: async () => runReactivateJob("PUBLISHING_CHECK"),
});

export const learningUpdate = schedules.task({
  id: "reactivate-learning-update",
  cron: { pattern: "0 18 * * *", timezone: "Africa/Johannesburg" },
  run: async () => runReactivateJob("LEARNING_UPDATE"),
});
