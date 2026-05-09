const { spawn } = require('child_process');
const readline = require('readline');

const child = spawn('node', ['/home/admin/github/lora-low-power-surveillance/tools/KiCAD-MCP-Server/dist/index.js'], {
  env: {
    ...process.env,
    KICAD_PYTHON: '/usr/bin/python3',
    PYTHONPATH: '/usr/lib/python3/dist-packages',
    LOG_LEVEL: 'info'
  }
});

const rl = readline.createInterface({
  input: child.stdout,
  output: child.stdin,
  terminal: false
});

let state = 0;

rl.on('line', (line) => {
  // console.log("RECV:", line);
  try {
    const msg = JSON.parse(line);
    if (msg.id === 1) {
      // Sent initialize, send initialized
      child.stdin.write(JSON.stringify({
        jsonrpc: "2.0",
        method: "notifications/initialized"
      }) + "\n");
      // Send tools/list
      child.stdin.write(JSON.stringify({
        jsonrpc: "2.0",
        id: 2,
        method: "tools/list",
        params: {}
      }) + "\n");
    } else if (msg.id === 2) {
      console.log("TOOLS:", JSON.stringify(msg.result.tools, null, 2));
      process.exit(0);
    }
  } catch (e) {}
});

child.stdin.write(JSON.stringify({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "test", version: "1.0.0" }
  }
}) + "\n");
