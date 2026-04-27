# SprintCycle

<div align="center">

**AI-Powered Agile Development Framework**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-0.1.0-orange.svg)](CHANGELOG.md)

English | [简体中文](README_CN.md)

</div>

---

## 📖 Product Overview

SprintCycle is an **AI-driven agile development framework** that automates the entire iteration lifecycle from requirements to deployment. It combines intelligent task planning, multi-agent collaboration, and continuous self-evolution to help developers build better software faster.

### Core Concept

```
Requirements (PRD) → Sprint Planning → Agent Execution → Verification → Knowledge Accumulation → Self-Evolution
```

SprintCycle doesn't just execute tasks—it learns from each iteration, continuously improving its capabilities and the quality of its output.

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

### 🔧 Extensible Architecture
- Plugin-based agent system
- Custom verification strategies
- Configurable tool integrations (Aider, Claude, Cursor)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/sprintcycle.git
cd sprintcycle

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy the configuration template
cp config.yaml.example config.yaml

# Set your API key (required for AI features)
export LLM_API_KEY=your_api_key_here
```

### Basic Usage

#### CLI Commands

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

#### Python API

```python
from sprintcycle.sprint_chain import SprintChain

# Initialize SprintChain
chain = SprintChain("/path/to/your/project")

# Generate Sprint plan from PRD
chain.auto_plan_from_prd("prd/requirements.yaml")

# Execute all Sprints
results = chain.run_all_sprints()

# Check results
for result in results:
    print(f"{result['sprint_name']}: {result['success']}/{result['total']}")

# View knowledge base statistics
stats = chain.get_kb_stats()
print(f"Total tasks: {stats['total']}, Success rate: {stats['success_rate']}%")
```

### Start Dashboard

```bash
# Start web dashboard
python cli.py dashboard --port 8088

# Or use uvicorn directly
uvicorn dashboard.server:app --host 0.0.0.0 --port 8088
```

Visit `http://localhost:8088` to access the dashboard.

---

## 📚 Documentation

### Getting Started
- [Quick Start Guide](docs/QUICKSTART.md) - Step-by-step tutorial
- [Configuration Guide](docs/CONFIGURATION.md) - Detailed configuration options

### Architecture
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Development Guide](docs/DEVELOPMENT.md) - How to extend SprintCycle

### API Reference
- [CLI Commands](docs/CLI_REFERENCE.md) - Complete CLI documentation
- [REST API](http://localhost:8088/docs) - Interactive API documentation (when dashboard is running)

### Advanced Topics
- [Creating Custom Agents](docs/CUSTOM_AGENTS.md) - Extend with your own agents
- [Verification Strategies](docs/VERIFICATION.md) - Implement custom verification
- [Self-Evolution Guide](docs/SELF_EVOLUTION.md) - Enable continuous improvement

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

## 📦 Project Structure

```
sprintcycle/
├── sprintcycle/           # Core framework
│   ├── chorus.py          # Agent coordinator
│   ├── sprint_chain.py    # Sprint execution chain
│   ├── optimizations.py   # Optimization utilities
│   ├── cache.py           # API response caching
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

### What this means:
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ✅ Patent grant included
- ❗ Must include license and copyright notice
- ❗ Must state changes made to files

---

## 🙏 Acknowledgments

Built with these amazing tools:

- [Aider](https://github.com/paul-gauthier/aider) - AI pair programming
- [Playwright](https://playwright.dev/) - Browser automation
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Loguru](https://github.com/Delgan/loguru) - Python logging

---

## 📮 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/sprintcycle/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/sprintcycle/discussions)

---

<div align="center">

**Made with ❤️ by the SprintCycle Team**

[⬆ Back to Top](#sprintcycle)

</div>
