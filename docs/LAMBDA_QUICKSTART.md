# Quick Start: Connect Claude to Boston OpenData MCP Server

This guide will help you connect Claude Desktop to the Boston OpenData MCP server that's already deployed on AWS Lambda.

## What You'll Need

Before you start, make sure you have:

1. **A computer** (Mac, Windows, or Linux)
2. **Python 3.10 or higher** (REQUIRED - older versions won't work)
   - Check your version: Open Terminal/Command Prompt and type `python3 --version`
   - **If you see Python 3.9 or lower**, you must upgrade Python first
   - Download the latest Python from [python.org](https://www.python.org/downloads/) (3.10+ required)
3. **Docker Desktop installed and running**
   - Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - **Important**: Docker must be running (not just installed) for the connection to work
   - Check if it's running: Open Docker Desktop app and wait until it says "Docker Desktop is running"
4. **Claude Desktop installed**
   - Download from [claude.ai/download](https://claude.ai/download)

## Step-by-Step Instructions

### Step 1: Open Terminal (Mac) or Command Prompt (Windows)

- **Mac**: Press `Cmd + Space`, type "Terminal", press Enter
- **Windows**: Press `Windows Key`, type "Command Prompt" or "PowerShell", press Enter

### Step 2: Install MCPEngine

**Option A: If you're working with the boston-core-mcp repository** (and have a `.venv` folder):

```bash
# Activate the virtual environment first
source .venv/bin/activate

# Then install mcpengine
pip install mcpengine
```

**Option B: If you're starting fresh** (no `.venv` folder):

```bash
python3 -m pip install mcpengine
```

**What this does**: Installs the tool needed to connect Claude to the MCP server.

**Wait for it to finish** - this may take 1-2 minutes. You'll see "Successfully installed" when it's done.

**Important**: If you see an error about Python version:

1. Your system Python is too old (need 3.10+)
2. Either upgrade your system Python from [python.org](https://www.python.org/downloads/)
3. Or create a virtual environment with Python 3.10+ first

### Step 3: Make Sure Docker is Running

**Before proceeding**, make sure Docker Desktop is running:

1. Open Docker Desktop application
2. Wait until you see "Docker Desktop is running" (green indicator)
3. You can verify by running in terminal: `docker ps` (should not show an error)

**If Docker is not running**, the connection will fail with a "Connection refused" error.

### Step 4: Connect Claude to the Server

**If you activated the virtual environment in Step 2** (you should see `(.venv)` in your terminal prompt), keep it active and run:

```bash
mcpengine proxy boston-opendata-lambda https://kdbjj7ebdewlcy24bt4wbf3uju0tjgdf.lambda-url.us-east-1.on.aws --mode http --claude
```

**If you didn't use the virtual environment**, just run the command above in your terminal.

**What this does**: Starts a connection between Claude and the Boston OpenData server.

**Important**:

- Once you run the command from above, you WILL NOT see any output (this is normal!). To verify this is running, run `docker ps` to verify that the proxy is running.
- **Keep this terminal window open** - don't close it! (You'll see `(.venv)` in the prompt if using the virtual environment)
- You can minimize it, but don't close it

### Step 5: Open Claude Desktop

1. Open Claude Desktop (the app you downloaded earlier)
2. Start a new conversation
3. You should see **Boston OpenData tools** available!

### Step 6: Test It Out

Try asking Claude something like:

- "Search for 311 datasets in Boston"
- "What datasets are available about parking?"
- "Show me information about crime data"

Claude will use the Boston OpenData tools automatically!

## Troubleshooting

### "ERROR: Could not find a version that satisfies the requirement mcpengine"

This means your Python version is too old. MCPEngine requires Python 3.10 or higher.

**Fix**:

1. Check your Python version:

   ```bash
   python3 --version
   ```

2. If it shows Python 3.9 or lower, you need to upgrade:
   - Download the latest Python from [python.org](https://www.python.org/downloads/)
   - Install it (make sure to check "Add Python to PATH" on Windows)
   - Close and reopen your terminal
   - Try Step 2 again

### "Command not found: pip" or "Command not found: python3"

**Fix**: Python might not be installed correctly. Try:

- Mac: Install Python 3.10+ from [python.org](https://www.python.org/downloads/), then try again
- Windows: Make sure Python was installed with "Add Python to PATH" checked

### "Command not found: mcpengine"

**Fix**: The installation might have failed. Try running Step 2 again with `python3 -m pip install mcpengine`.

### "Connection refused" or "ConnectionRefusedError"

**Fix**: Docker Desktop is not running.

1. Open Docker Desktop application
2. Wait until it fully starts (shows "Docker Desktop is running")
3. Verify with: `docker ps` (should not show an error)
4. Try the connection command again

### "Cannot connect" or "Connection failed"

**Fix**:

1. Make sure you copied the entire command in Step 4 (it's very long!)
2. Make sure there are no extra spaces
3. Make sure your internet connection is working
4. Try running the command again

### Claude doesn't show the tools

**Fix**:

1. Make sure the terminal with the proxy is still running (Step 4)
2. Make sure Docker Desktop is running
3. **Completely close and restart Claude Desktop**
4. Make sure you're starting a new conversation

### The terminal command stops working

**Fix**: Just run Step 4 again. Sometimes the connection drops - this is normal.

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
2. Press `Ctrl + C` (not `Cmd + C` on Mac - use `Ctrl`)
3. The connection will stop
4. If you used the virtual environment, you can deactivate it with: `deactivate`

To reconnect later:

- If using the virtual environment, first run `source .venv/bin/activate`
- Then run the proxy command from Step 4 again

## Need Help?

If you're stuck:

1. Check the troubleshooting section above
2. Make sure all steps were completed
3. Try closing everything and starting over from Step 3

---

**That's it!** You're now connected to the Boston OpenData MCP server. Enjoy exploring Boston's data with Claude!
