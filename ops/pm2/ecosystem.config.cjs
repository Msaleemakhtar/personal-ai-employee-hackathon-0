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
      // Restart policy: max 10 restarts in 1 minute window
      // After that, wait 1 minute before attempting restart
      max_restarts: 10,
      min_uptime: 10000, // Process must stay up 10 seconds to be considered stable
      restart_delay: 5000, // Wait 5 seconds between restarts
      exp_backoff_restart_delay: 100, // Exponential backoff starting at 100ms
      max_memory_restart: "200M", // Restart if memory usage exceeds 200MB
      kill_timeout: 5000, // Wait 5 seconds for graceful shutdown before SIGKILL
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
      // More lenient restart policy for orchestrator (may call Claude CLI)
      max_restarts: 10,
      min_uptime: 10000,
      restart_delay: 5000,
      exp_backoff_restart_delay: 100,
      max_memory_restart: "300M", // Higher memory limit (Claude CLI subprocess)
      kill_timeout: 10000, // Longer grace period (may have subprocess running)
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
    {
      name: "ai-employee-gmail-watcher",
      cwd: "/home/salim/Desktop/hackathon0/apps/ai_employee",
      script: "uv",
      args: "run python -m ai_employee.watchers.gmail_watcher",
      autorestart: true,
      // More lenient restart policy (network errors are expected)
      max_restarts: 15,
      min_uptime: 30000, // Must stay up 30 seconds to be considered stable
      restart_delay: 10000, // Wait 10 seconds between restarts
      exp_backoff_restart_delay: 1000, // Start backoff at 1 second
      max_memory_restart: "250M",
      kill_timeout: 5000,
      env: {
        VAULT_PATH: process.env.VAULT_PATH,
      },
    },
  ],
};
