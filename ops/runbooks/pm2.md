# PM2 Runbook (Hackathon 0)

Config:
- `/home/salim/Desktop/hackathon0/ops/pm2/ecosystem.config.cjs`

## Install PM2
```bash
npm i -g pm2
```

## Start processes
```bash
pm2 start /home/salim/Desktop/hackathon0/ops/pm2/ecosystem.config.cjs
pm2 status
```

## View logs
```bash
pm2 logs ai-employee-filesystem-watcher
pm2 logs ai-employee-orchestrator
```

## Persist across reboot
```bash
pm2 save
pm2 startup
# Follow instructions PM2 prints
```

## Stop / restart
```bash
pm2 stop ai-employee-filesystem-watcher ai-employee-orchestrator
pm2 restart ai-employee-filesystem-watcher ai-employee-orchestrator
```
