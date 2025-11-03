# Quick Start: Connect Claude to Boston OpenData MCP Server

This guide will help you connect Claude Desktop to the Boston OpenData MCP server that's already deployed on AWS Lambda.

## What You'll Need

Before you start, make sure you have:

1. **A computer** (Mac, Windows, or Linux)
2. **Python installed** (version 3.10 or higher)
   - Check if you have it: Open Terminal/Command Prompt and type `python --version`
   - If not installed: Download from [python.org](https://www.python.org/downloads/)
3. **Claude Desktop installed**
   - Download from [claude.ai/download](https://claude.ai/download)

## Step-by-Step Instructions

### Step 1: Open Terminal (Mac) or Command Prompt (Windows)

- **Mac**: Press `Cmd + Space`, type "Terminal", press Enter
- **Windows**: Press `Windows Key`, type "Command Prompt" or "PowerShell", press Enter

### Step 2: Install MCPEngine

Copy and paste this command into your terminal, then press Enter:

```bash
pip install mcpengine[cli,lambda]
```

**What this does**: Installs the tool needed to connect Claude to the MCP server.

**Wait for it to finish** - this may take 1-2 minutes. You'll see "Successfully installed" when it's done.

### Step 3: Connect Claude to the Server

Copy and paste this **entire command** into your terminal, then press Enter:

```bash
mcpengine proxy boston-opendata-lambda https://kdbjj7ebdewlcy24bt4wbf3uju0tjgdf.lambda-url.us-east-1.on.aws/ --mode http --claude
```

**What this does**: Starts a connection between Claude and the Boston OpenData server.

**Important**:

- You'll see some messages like "Starting proxy..." or "Connected"
- **Leave this terminal window open** - don't close it!
- You can minimize it, but don't close it

### Step 4: Open Claude Desktop

1. Open Claude Desktop (the app you downloaded earlier)
2. Start a new conversation
3. You should see **Boston OpenData tools** available!

### Step 5: Test It Out

Try asking Claude something like:

- "Search for 311 datasets in Boston"
- "What datasets are available about parking?"
- "Show me information about crime data"

Claude will use the Boston OpenData tools automatically!

## Troubleshooting

### "Command not found: pip"

**Fix**: Python might not be installed correctly. Try:

- Mac: `python3 -m pip install mcpengine[cli,lambda]`
- Windows: Make sure Python was installed with "Add Python to PATH" checked

### "Command not found: mcpengine"

**Fix**: The installation might have failed. Try running Step 2 again.

### "Cannot connect" or "Connection failed"

**Fix**:

1. Make sure you copied the entire command in Step 3 (it's very long!)
2. Make sure there are no extra spaces
3. Make sure your internet connection is working
4. Try running the command again

### Claude doesn't show the tools

**Fix**:

1. Make sure the terminal with the proxy is still running (Step 3)
2. **Completely close and restart Claude Desktop**
3. Make sure you're starting a new conversation

### The terminal command stops working

**Fix**: Just run Step 3 again. Sometimes the connection drops - this is normal.

## Using the Tools

Once connected, Claude has access to these Boston OpenData tools:

1. **Search datasets** - Find datasets using keywords
2. **List all datasets** - See everything available
3. **Get dataset info** - Detailed information about a specific dataset
4. **Query data** - Get actual data from datasets
5. **Get schema** - See the structure of datasets

Just ask Claude naturally - it will automatically use the right tool!

## Stopping the Connection

When you're done:

1. Go back to the terminal window
2. Press `Ctrl + C` (Mac: `Cmd + C`)
3. The connection will stop

To reconnect later, just run Step 3 again.

## Need Help?

If you're stuck:

1. Check the troubleshooting section above
2. Make sure all steps were completed
3. Try closing everything and starting over from Step 3

---

**That's it!** You're now connected to the Boston OpenData MCP server. Enjoy exploring Boston's data with Claude!
