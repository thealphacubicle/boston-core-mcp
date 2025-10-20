# DEVELOPMENT.md

Overview

This document explains, in plain language for beginners, how the MCP server in this repository was developed and how to run it locally. It includes a concrete example showing how to connect the running MCP server to Claude Desktop.

If you are new to programming, follow the steps in order. If something is unclear, ask and I'll clarify.

1) What this repository contains

- A server ("MCP server") that provides the core backend for the project. The exact language or framework may vary; this document tells you how to detect and run it.
- Source code, configuration files, and tests.

2) Before you start (prerequisites)

You will need:
- Git installed (to clone the repo). Check with: git --version
- One or more runtime/tooling depending on the project language. To figure out which, look for one of these files in the repository root:
  - package.json  => Node.js / JavaScript / TypeScript
  - requirements.txt or pyproject.toml => Python
  - pom.xml or build.gradle => Java
  - Cargo.toml => Rust
  - Makefile => helpful targets may be provided

Install the corresponding runtime:
- Node.js (recommend LTS) and npm/yarn: https://nodejs.org/
- Python 3.8+: https://python.org/
- Java 11+ for Maven/Gradle projects: https://adoptopenjdk.net/
- Rust: https://rustup.rs/

Also helpful:
- A code editor (VS Code recommended): https://code.visualstudio.com/
- ngrok (optional) to expose your local server to the internet for external tools like Claude Desktop: https://ngrok.com/

3) Clone the repository

Open a terminal and run:

  git clone https://github.com/thealphacubicle/boston-core-mcp.git
  cd boston-core-mcp

4) Identify how to run the server

Check repository root for the files listed above. Follow the appropriate section below based on what you find.

A) If this is a Node.js project (package.json)

- Install dependencies:

  npm install
  # or if the project uses yarn:
  yarn install

- Check package.json scripts for a start script. Common commands:

  npm run start
  npm run dev   # often for a developer server with hot reload

B) If this is a Python project (requirements.txt or pyproject.toml)

- Create and activate a virtual environment (recommended):

  python3 -m venv venv
  source venv/bin/activate   # macOS / Linux
  venv\Scripts\activate    # Windows PowerShell

- Install dependencies:

  pip install -r requirements.txt
  # or if pyproject with poetry:
  poetry install

- Run the server using the documented command (often something like):

  python -m app
  # or
  gunicorn app:app --reload

C) If this is a Java project (pom.xml or build.gradle)

- For Maven:

  mvn clean install
  mvn spring-boot:run     # if it is a Spring Boot project

- For Gradle:

  ./gradlew build
  ./gradlew bootRun

D) Other languages

- Follow the standard build/run steps for the language (use README or project files).

5) Configuration (environment variables and ports)

- Look for an .env.example, config/*.yml or config/*.json files. If there is no example, you can create an .env file in the project root.

Example .env (create in repo root):

  # Port the server listens on
  PORT=8080

  # Optional API key if the server uses authentication for external tools
  API_KEY=some-secret-token

- The server will usually read PORT and API_KEY. Adjust values if the server uses other names.

6) Start the server locally

- After installing dependencies and configuring env vars, run the start command from step 4 for your project type.
- Wait for a log line that says the server is listening (example: "Server listening on http://localhost:8080").

7) Test the server works locally

- Open a browser and visit http://localhost:8080 (or the configured port).
- Or use curl to check an endpoint (example):

  curl -i http://localhost:8080/health

- If you get a 200 or a JSON response, the server is running.

8) Example: Connecting the MCP server to Claude Desktop

This is a practical example showing one way to connect a local MCP server to Claude Desktop. Claude Desktop is an application that can call external servers or plugins. Exact UI labels can vary by version; treat the following as a clear, concrete example you can adapt.

Goal: Make Claude Desktop send requests to your local MCP server.

Option 1 — Local direct connection (if Claude Desktop can reach localhost)

1. Start your server on a known port, e.g., 8080.
2. In Claude Desktop, go to Settings (or Preferences) and find where you can add a custom API/Plugin/Server. If there is a "Custom Server" or "Add Plugin" button, choose it.
3. For the server URL, enter: http://localhost:8080
4. If the server requires an API key, add a header named Authorization with value Bearer <API_KEY> (replace <API_KEY> with the value you put in .env).
5. Save settings and try the integration: trigger the plugin or request to the server. Check your server logs to see incoming requests.

Notes:
- Some desktop apps sandbox network access and may not allow calls to localhost. If Claude Desktop does not reach your local server using http://localhost, try Option 2 below.

Option 2 — Use ngrok to expose your local server publicly

If Claude Desktop runs in an environment that cannot access your machine's localhost, ngrok creates a public URL that tunnels to your local server.

1. Install ngrok and sign up for an account (optional but recommended for stable subdomains).
2. Run ngrok on your server port (example):

  ngrok http 8080

3. ngrok will give you a public URL, e.g. https://abcd-12-34-56.ngrok.io
4. In Claude Desktop "Add Server" UI, use that ngrok URL as the base URL.
5. Set headers (Authorization) if needed.
6. Try sending requests; you should see requests appear in both Claude Desktop and the server logs.

Security note: Exposing your local server to the internet can be risky. Use API keys or other protections and stop ngrok when testing is done.

9) How the server was developed (high-level, plain language)

- The server was built as a small backend that listens for HTTP requests and responds with data. Developers typically:
  1. Pick a language and framework (Node.js + Express, Python + FastAPI/Flask, Java + Spring Boot, etc.).
  2. Define routes/endpoints that accept requests and return responses.
  3. Add authentication if needed (API keys or tokens).
  4. Add configuration files so settings (like PORT and API_KEY) are not hard-coded.
  5. Add logging so developers can see incoming requests and errors.
  6. Write tests for important behaviors.

- Look through the repository for code that defines the HTTP server (files named server.js, app.js, main.py, Application.java, etc.). Reading the top-level file often shows how the server starts and which port and config keys it reads.

10) Troubleshooting tips

- Port already in use: change PORT in .env or kill the process using the port (lsof -i :8080 or netstat).
- 403/401 errors from Claude Desktop: make sure Authorization header matches the server's expected token.
- CORS errors in a browser: enable CORS in the server or test with curl (servers must explicitly allow requests from other origins).
- If Claude Desktop cannot reach localhost, use ngrok as shown above.

11) Making small changes and testing

- Edit code in your editor. Re-run the server or use auto-reload tools (nodemon for Node.js, uvicorn --reload for FastAPI).
- Add console logs or print statements to help understand code flow.

12) Contributing

- Follow existing code style and patterns in the repository.
- Add tests for new behavior.
- Open a pull request with a clear title and description.

13) Where to look in the code for key pieces (beginner guide)

- Server entrypoint: search for files with names like server.js, index.js, app.js, main.py, Application.java.
- Routes / endpoints: look for directories named routes, controllers, api, or files that export request handlers.
- Configuration: look for .env.example, config/, or files that parse process.env (Node) or os.environ (Python).
- Authentication: look for middleware functions or code that checks headers for an API key.

14) Example .env.example to commit (copy this into .env for local testing)

  PORT=8080
  API_KEY=changeme

15) Final notes

- This document is intentionally general so it helps beginners work with this repo even if the project uses a different language. If you want, I can update this file with exact commands tailored to the language used in the repository (e.g., Node.js commands) if you tell me which files exist (package.json, requirements.txt, etc.) or let me read the repo.

Thank you — if you want I can also add a short quick-start script or a Makefile to automate these steps.
