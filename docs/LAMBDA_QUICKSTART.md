# Quick Start: Connect Claude to Boston OpenData MCP Server

This guide will help you connect Claude Desktop to the Boston OpenData MCP server that's already deployed on AWS Lambda.

## What You'll Need

Before you start, make sure you have:

1. **A computer** (Mac, Windows, or Linux)
2. **Docker Desktop installed and running**
   - Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - **Important**: Docker must be running (not just installed) for the connection to work
   - Check if it's running: Open Docker Desktop app and wait until it says "Docker Desktop is running"
3. **Claude Desktop installed**
   - Download from [claude.ai/download](https://claude.ai/download)

## Step-by-Step Instructions

### Step 1: Install Python (Mac users only)

If you're on Mac and don't have Python 3.10 or higher, install it using Homebrew:

**First, install Homebrew** (if you don't have it):

1. Open Terminal: Press `Cmd + Space`, type "Terminal", press Enter
2. Run this command:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Follow the on-screen instructions

**Then install Python**:

```bash
brew install python@3.14
```

**Windows/Linux users**: Download Python 3.10 or higher from [python.org](https://www.python.org/downloads/) and install it.

### Step 2: Open Terminal (Mac) or Command Prompt (Windows)

- **Mac**: Press `Cmd + Space`, type "Terminal", press Enter
- **Windows**: Press `Windows Key`, type "Command Prompt" or "PowerShell", press Enter

### Step 3: Install pipx and mcpengine

**Mac users**, run these commands one at a time:

```bash
# Install pipx (a tool for installing Python applications)
brew install pipx

# Install mcpengine with CLI support
pipx install 'mcpengine[cli]'
```

**Windows/Linux users**, run:

```bash
# Install pipx
python3 -m pip install --user pipx

# Add pipx to PATH (you may need to restart your terminal after this)
python3 -m pipx ensurepath

# Install mcpengine with CLI support
pipx install 'mcpengine[cli]'
```

**What this does**: Installs the tool needed to connect Claude to the MCP server.

**Wait for it to finish** - you'll see "done! ✨ 🌟 ✨" when it's complete.

### Step 4: Make Sure Docker is Running

**Before proceeding**, make sure Docker Desktop is running:

1. Open Docker Desktop application
2. Wait until you see "Docker Desktop is running" (green indicator)
3. You can verify by running in terminal: `docker ps` (should not show an error)

**If Docker is not running**, the connection will fail with a "Connection refused" error.

### Step 5: Connect Claude to the Server

Run this command in your terminal:

```bash
mcpengine proxy boston-opendata-lambda https://kdbjj7ebdewlcy24bt4wbf3uju0tjgdf.lambda-url.us-east-1.on.aws --mode http --claude
```

**What this does**: Starts a connection between Claude and the Boston OpenData server.

**Important**:

- Once you run this command, you **will NOT see any output** (this is normal!)
- To verify it's running, open a new terminal window and run `docker ps` - you should see a container running
- **Keep this terminal window open** - don't close it!
- You can minimize it, but don't close it or the connection will stop

### Step 6: Open Claude Desktop

1. Open Claude Desktop (the app you downloaded earlier)
2. **Completely restart Claude Desktop** if it was already open (quit and reopen it)
3. Start a new conversation
4. You should see **Boston OpenData tools** available in the tool selector!

### Step 7: Test It Out

Try asking Claude something like:

- "Search for 311 datasets in Boston"
- "What datasets are available about parking?"
- "Show me information about crime data"

Claude will use the Boston OpenData tools automatically!

## Troubleshooting

### "Command not found: brew" (Mac)

**Fix**: You need to install Homebrew first. See Step 1 above.

### "Command not found: pipx"

**Fix**: The installation might have failed. Try running Step 3 again.

### "Error: cli feature is required"

**Fix**: You installed mcpengine without the CLI extras. Run:

```bash
pipx install --force 'mcpengine[cli]'
```

### "zsh: no matches found: mcpengine[cli]" (Mac)

**Fix**: You need quotes around the package name. Use:

```bash
pipx install 'mcpengine[cli]'
```

### "Connection refused" or "ConnectionRefusedError"

**Fix**: Docker Desktop is not running.

1. Open Docker Desktop application
2. Wait until it fully starts (shows "Docker Desktop is running")
3. Verify with: `docker ps` (should not show an error)
4. Try the connection command again

### "Cannot connect" or "Connection failed"

**Fix**:

1. Make sure you copied the entire command in Step 5 (it's very long!)
2. Make sure there are no extra spaces
3. Make sure your internet connection is working
4. Try running the command again

### Claude doesn't show the tools

**Fix**:

1. Make sure the terminal with the proxy is still running (Step 5)
2. Make sure Docker Desktop is running
3. **Completely quit and restart Claude Desktop** (don't just close the window)
4. Start a new conversation
5. Check the tool selector in Claude Desktop

### The terminal command stops working

**Fix**: Just run Step 5 again. Sometimes the connection drops - this is normal.

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

1. Go back to the terminal window where the proxy is running
2. Press `Ctrl + C` (not `Cmd + C` on Mac - use `Ctrl`)
3. The connection will stop

To reconnect later, just run the command from Step 5 again.

## Need Help?

If you're stuck:

1. Check the troubleshooting section above
2. Make sure all steps were completed in order
3. Make sure Docker Desktop is running
4. Try completely restarting Claude Desktop
5. Try closing everything and starting over from Step 4

---

**That's it!** You're now connected to the Boston OpenData MCP server. Enjoy exploring Boston's data with Claude!
