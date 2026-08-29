#!/usr/bin/env node
/**
 * AI Daily Pulse - Metrics 统计
 * 用法: node metrics.js [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--json]
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const LOG_FILE = path.join(DATA_DIR, 'log.json');

function parseArgs() {
  const args = process.argv.slice(2);
  const result = { from: null, to: null, json: false };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--from' && args[i + 1]) {
      result.from = args[++i];
    } else if (args[i] === '--to' && args[i + 1]) {
      result.to = args[++i];
    } else if (args[i] === '--json') {
      result.json = true;
    }
  }

  return result;
}

function loadLogs() {
  if (!fs.existsSync(LOG_FILE)) {
    return [];
  }
  try {
    const data = fs.readFileSync(LOG_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (e) {
    return [];
  }
}

function filterByDate(logs, from, to) {
  return logs.filter((entry) => {
    const date = entry.timestamp ? entry.timestamp.slice(0, 10) : '';
    if (from && date < from) return false;
    if (to && date > to) return false;
    return true;
  });
}

function computeMetrics(logs) {
  if (logs.length === 0) {
    return {
      total_runs: 0,
      successful_runs: 0,
      failed_runs: 0,
      total_collected: 0,
      total_pushed: 0,
      avg_collected_per_run: 0,
      avg_pushed_per_run: 0,
      avg_duration_seconds: 0,
      error_breakdown: {},
      tier_breakdown: {},
    };
  }

  const totalRuns = logs.length;
  const successfulRuns = logs.filter((l) => l.pushed > 0).length;
  const failedRuns = logs.filter((l) => l.error).length;

  const totalCollected = logs.reduce((s, l) => s + (l.total_collected || 0), 0);
  const totalPushed = logs.reduce((s, l) => s + (l.pushed || 0), 0);

  const avgCollected = Math.round(totalCollected / totalRuns);
  const avgPushed = Math.round(totalPushed / totalRuns);

  const durations = logs.map((l) => l.duration_seconds || 0);
  const avgDuration = Math.round((durations.reduce((s, d) => s + d, 0) / totalRuns) * 10) / 10;

  // Error breakdown
  const errorBreakdown = {};
  logs.forEach((l) => {
    if (l.error) {
      errorBreakdown[l.error] = (errorBreakdown[l.error] || 0) + 1;
    }
  });

  // Tier breakdown
  const tierBreakdown = {};
  logs.forEach((l) => {
    const tier = `tier_${l.tier || 'unknown'}`;
    if (!tierBreakdown[tier]) {
      tierBreakdown[tier] = { runs: 0, collected: 0, pushed: 0 };
    }
    tierBreakdown[tier].runs++;
    tierBreakdown[tier].collected += l.total_collected || 0;
    tierBreakdown[tier].pushed += l.pushed || 0;
  });

  return {
    total_runs: totalRuns,
    successful_runs: successfulRuns,
    failed_runs: failedRuns,
    total_collected: totalCollected,
    total_pushed: totalPushed,
    avg_collected_per_run: avgCollected,
    avg_pushed_per_run: avgPushed,
    avg_duration_seconds: avgDuration,
    error_breakdown: errorBreakdown,
    tier_breakdown: tierBreakdown,
  };
}

function main() {
  const args = parseArgs();
  const logs = loadLogs();
  const filtered = filterByDate(logs, args.from, args.to);
  const metrics = computeMetrics(filtered);

  // 添加查询范围信息
  metrics.query = {
    from: args.from || 'all',
    to: args.to || 'all',
    entries_in_range: filtered.length,
  };

  if (args.json) {
    console.log(JSON.stringify(metrics, null, 2));
  } else {
    console.log('=== AI Daily Pulse Metrics ===');
    console.log(`Period: ${args.from || 'start'} ~ ${args.to || 'now'}`);
    console.log(`Total runs: ${metrics.total_runs}`);
    console.log(`Successful: ${metrics.successful_runs}`);
    console.log(`Failed: ${metrics.failed_runs}`);
    console.log(`Total collected: ${metrics.total_collected}`);
    console.log(`Total pushed: ${metrics.total_pushed}`);
    console.log(`Avg collected/run: ${metrics.avg_collected_per_run}`);
    console.log(`Avg pushed/run: ${metrics.avg_pushed_per_run}`);
    console.log(`Avg duration: ${metrics.avg_duration_seconds}s`);

    if (Object.keys(metrics.error_breakdown).length > 0) {
      console.log('\nErrors:');
      for (const [err, count] of Object.entries(metrics.error_breakdown)) {
        console.log(`  ${err}: ${count}`);
      }
    }

    if (Object.keys(metrics.tier_breakdown).length > 0) {
      console.log('\nBy Tier:');
      for (const [tier, data] of Object.entries(metrics.tier_breakdown)) {
        console.log(`  ${tier}: ${data.runs} runs, ${data.collected} collected, ${data.pushed} pushed`);
      }
    }
  }
}

main();
