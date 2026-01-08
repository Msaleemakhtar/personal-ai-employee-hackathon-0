// Load environment variables from .env file
// dotenv is installed in ops/node_modules
require('/home/salim/Desktop/hackathon0/ops/node_modules/dotenv').config({ path: '/home/salim/Desktop/hackathon0/.env' });

module.exports = {
  apps: [
    {
      name: "ai-employee-filesystem-watcher",
      cwd: "/home/salim/Desktop/hackathon0/apps/ai_employee",
      script: "uv",
      args: "run python -m ai_employee.watchers.filesystem_watcher",
      autorestart: true,
      max_restarts: 50,
      env: {
        VAULT_PATH: process.env.VAULT_PATH,
        INBOX_PATH: process.env.INBOX_PATH,
        NEEDS_ACTION_PATH: process.env.NEEDS_ACTION_PATH,
        DONE_PATH: process.env.DONE_PATH,
        LOGS_PATH: process.env.LOGS_PATH,
      },
    },
    {
      name: "ai-employee-orchestrator",
      cwd: "/home/salim/Desktop/hackathon0/apps/ai_employee",
      script: "uv",
      args: "run python -m ai_employee.orchestrator",
      autorestart: true,
      max_restarts: 50,
      env: {
        VAULT_PATH: process.env.VAULT_PATH,
        INBOX_PATH: process.env.INBOX_PATH,
        NEEDS_ACTION_PATH: process.env.NEEDS_ACTION_PATH,
        DONE_PATH: process.env.DONE_PATH,
        LOGS_PATH: process.env.LOGS_PATH,
        // Mode: "queue" (Pro plan - manual triage) or "auto" (API access - autonomous)
        ORCHESTRATOR_MODE: process.env.ORCHESTRATOR_MODE || "queue",
        // API key (only needed for auto mode)
        ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
      },
    },
  ],
};
