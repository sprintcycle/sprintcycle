# SprintCycle

<div align="center">

**AI-Powered Agile Development Framework**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-0.2.0-orange.svg)](CHANGELOG.md)

English | [简体中文](README_CN.md)

</div>

---

## 📖 Product Overview

SprintCycle is an **AI-driven agile development framework** that automates the entire iteration lifecycle from requirements to deployment. It combines intelligent task planning, multi-agent collaboration, and continuous self-evolution to help developers build better software faster.

### Core Concept

```
Requirements (PRD) → Sprint Planning → Agent Execution → Verification → Knowledge Accumulation → Self-Evolution
```

---

## 🎯 Two Ways to Use SprintCycle

SprintCycle can be triggered in **two flexible ways**:

### Way 1: CLI (Command Line Interface)

Direct command-line usage for local development and automation:

```bash
# Initialize a project
sprintcycle init -p /path/to/project

# Execute from PRD
sprintcycle run -p /path/to/project --prd requirements.yaml

# Run self-evolution cycle
sprintcycle sprint auto-run -p /path/to/project
```

**Best for**: Local development, CI/CD pipelines, automation scripts

### Way 2: OpenClaw Skill + MCP (Recommended for AI Agents)

Trigger SprintCycle through OpenClaw skills with MCP (Model Context Protocol) integration:

```python
# In your AI agent (e.g., Coze/Claude/GPT)
# Simply describe what you want to build

"Use SprintCycle to develop a tech news website with:
- Frontend: news list and detail pages
- Backend: FastAPI with SQLite
- Features: view history, filter by category"

# SprintCycle MCP tools will be automatically invoked:
# - sprintcycle_init
# - sprintcycle_plan_from_prd
# - sprintcycle_run_sprint
# - sprintcycle_verify_playwright
```

**Best for**: AI-powered development, natural language workflows, intelligent automation

| Feature | CLI | OpenClaw + MCP |
|---------|-----|----------------|
| Local development | ✅ | ✅ |
| Natural language input | ❌ | ✅ |
| AI agent integration | ❌ | ✅ |
| Automated planning | Manual | ✅ Auto |
| Best for | Developers | AI Agents |

---

## ✨ Key Features

### 🔄 Multi-Round Iteration
- Sprint-style development with automatic task breakdown
- Support for iterative refinement and bug fixes
- Transaction-based rollback mechanism

### 🤖 Multi-Agent Collaboration
| Agent | Role | Capabilities |
|-------|------|--------------|
| CODER | Code Implementation | Features, refactoring, bug fixes |
| REVIEWER | Code Review | PR review, code quality, best practices |
| ARCHITECT | Architecture Design | Technical specs, API design, system design |
| TESTER | Testing | Unit tests, integration tests, test coverage |
| DIAGNOSTIC | Problem Diagnosis | Root cause analysis, debugging, log analysis |
| UI_VERIFY | UI Verification | Screenshot comparison, accessibility checks |

### ✅ Intelligent Verification
- **Five-Source Verification**: Test results, code review, runtime, UI, and diff verification
- **Playwright Integration**: Automated UI testing and visual regression
- **Code Quality Checks**: Linting, type checking, complexity analysis

### 📚 Knowledge Base
- Automatic experience accumulation from each iteration
- Task success/failure pattern learning
- Reusable solutions and best practices

### 🧬 Self-Evolution
SprintCycle can evolve itself through a 9-phase closed-loop:

1. **Roadmap Extraction** - Analyze history, extract evolution patterns
2. **PRD Generation** - Auto-generate next-phase requirements
3. **Iteration Execution** - Execute development tasks
4. **Product Evaluation** - Measure product improvements
5. **Framework Evaluation** - Assess framework performance
6. **Bug Fixing** - Discover and fix framework bugs
7. **Framework Optimization** - Enhance capabilities
8. **Integration Testing** - Validate changes
9. **Self-Iteration** - Update evolution skills

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy the configuration template
cp config.yaml.example config.yaml

# Set your LLM API key
export LLM_API_KEY=your_api_key_here
```

### Usage (CLI)

```bash
# Initialize a project
python cli.py init -p /path/to/your/project

# Check project status
python cli.py status -p /path/to/your/project

# Execute a single task
python cli.py run -p /path/to/your/project -t "Implement user authentication"

# Execute from PRD
python cli.py run -p /path/to/your/project --prd prd/requirements.yaml

# Run self-evolution cycle
python cli.py sprint auto-run -p /path/to/your/project
```

### Usage (OpenClaw + MCP)

In your AI agent (Coze, Claude, etc.) with OpenClaw skill installed:

```
User: "Build a blog system with user authentication and post management"

AI Agent: 
  → Calls sprintcycle_init
  → Calls sprintcycle_plan_from_prd (auto-generates PRD)
  → Calls sprintcycle_auto_run
  → Calls sprintcycle_playwright_verify
  → Returns completed project
```

---

## 📚 Documentation

### Getting Started
- [Quick Start Guide](docs/QUICKSTART.md) - Step-by-step tutorial
- [Configuration Guide](docs/CONFIGURATION.md) - Detailed configuration options

### Architecture
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Development Guide](docs/DEVELOPMENT.md) - How to extend SprintCycle

### API Reference
- [CLI Commands](#cli-reference) - Complete CLI documentation
- [MCP Tools](#mcp-tools) - All 18 MCP tools
- [REST API](http://localhost:8088/docs) - Interactive API docs (when dashboard is running)

---

## 🛠️ CLI Reference

| Command | Description |
|---------|-------------|
| `init` | Initialize SprintCycle in a project |
| `status` | View project status and statistics |
| `run` | Execute tasks or PRD iterations |
| `sprint plan` | View Sprint planning |
| `sprint create` | Create a new Sprint |
| `sprint run` | Execute a specific Sprint |
| `sprint auto-run` | Execute all pending Sprints |
| `verify playwright` | Run Playwright UI verification |
| `verify frontend` | Run frontend accessibility check |
| `scan` | Scan project for issues |
| `autofix` | Automatically fix detected issues |
| `rollback` | Rollback recent changes |
| `knowledge show` | View knowledge base |
| `dashboard` | Start web dashboard |

---

## 🔌 MCP Tools

SprintCycle provides **18 MCP tools** for AI agent integration:

### Project Management
| Tool | Description |
|------|-------------|
| `sprintcycle_list_projects` | List all SprintCycle projects |
| `sprintcycle_list_tools` | List available execution tools |
| `sprintcycle_status` | Get project status |

### Sprint Management
| Tool | Description |
|------|-------------|
| `sprintcycle_get_sprint_plan` | Get Sprint plan |
| `sprintcycle_create_sprint` | Create a new Sprint |
| `sprintcycle_run_sprint` | Execute a Sprint |
| `sprintcycle_run_sprint_by_name` | Execute Sprint by name |
| `sprintcycle_auto_run` | Auto-execute all Sprints |
| `sprintcycle_plan_from_prd` | Generate Sprint from PRD |

### Task Execution
| Tool | Description |
|------|-------------|
| `sprintcycle_run_task` | Execute a single task |

### Verification
| Tool | Description |
|------|-------------|
| `sprintcycle_playwright_verify` | Playwright UI verification |
| `sprintcycle_verify_frontend` | Frontend verification |
| `sprintcycle_verify_visual` | Visual regression testing |

### Issue Management
| Tool | Description |
|------|-------------|
| `sprintcycle_scan_issues` | Scan project issues |
| `sprintcycle_autofix` | Auto-fix issues |
| `sprintcycle_rollback` | Rollback changes |

### Knowledge Base
| Tool | Description |
|------|-------------|
| `sprintcycle_get_kb_stats` | Knowledge base statistics |
| `sprintcycle_get_execution_detail` | Execution details |

---

## 📦 Project Structure

```
sprintcycle/
├── sprintcycle/           # Core framework
│   ├── chorus.py          # Agent coordinator
│   ├── sprint_chain.py    # Sprint execution chain
│   ├── optimizations.py   # Optimization utilities
│   └── agents/            # Agent implementations
├── dashboard/             # Web dashboard
│   └── server.py          # FastAPI server
├── tests/                 # Test suite
├── docs/                  # Documentation
├── cli.py                 # Command-line interface
├── config.yaml.example    # Configuration template
└── requirements.txt       # Dependencies
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please read our [Contributing Guide](CONTRIBUTING.md) for details.

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with these amazing tools:

- [Aider](https://github.com/paul-gauthier/aider) - AI pair programming
- [Playwright](https://playwright.dev/) - Browser automation
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

---

<div align="center">

**Made with ❤️ by the SprintCycle Team**

[⬆ Back to Top](#sprintcycle)

</div>
