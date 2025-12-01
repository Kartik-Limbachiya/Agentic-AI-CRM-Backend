# Agentic AI CRM Backend 🤖📊

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Agents-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

An autonomous **AI-powered CRM Backend** designed to plan, execute, and analyze marketing campaigns. Built with **LangGraph** and **Google Gemini**, this system uses a multi-agent workflow to automate social media strategies from conception to reporting.

---

## 🚀 Key Features

- **🧠 Autonomous Planning**: Uses **Google Gemini 2.5 Flash** to generate high-impact content strategies for LinkedIn, YouTube, and Threads.
- **🔄 Stateful Workflows**: Implements **LangGraph** for managing complex, cyclic agent behaviors (Plan → Execute → Report).
- **🔌 Multi-Mode Execution**:
  - **Live Mode**: Posts directly to social media using the **Ayrshare API**.
  - **Simulation Mode**: Runs a sophisticated mock execution with simulated engagement metrics for testing/demo purposes.
- **📊 AI-Driven Reporting**: Analyzes campaign performance and generates executive summaries with actionable insights.
- **⚡ High Performance**: Built on **FastAPI** with full asynchronous support.
- **🐳 Production Ready**: Dockerized application with CI/CD pipelines via GitHub Actions.

---

## 🏗️ Architecture

The system operates on a 3-node graph architecture:

1.  **Planner Node (`Strategist`)** 📝
    - Analyzes brand goals and target audience.
    - Generates 3 platform-specific posts with content and image ideas.
    - Outputs a structured JSON plan.

2.  **Executor Node (`Doer`)** 🚀
    - Validates the plan.
    - Publishes content via external APIs (or simulates publishing).
    - Tracks likes, shares, and impressions (real or mocked).

3.  **Reporter Node (`Analyst`)** 📈
    - Aggregates execution data.
    - Calculates engagement rates.
    - Generates a markdown performance report using LLM analysis.

---

## 🛠️ Tech Stack

- **Core Framework**: FastAPI, Uvicorn
- **AI & Orchestration**: LangChain, LangGraph, Google Gemini (via `langchain-google-genai`)
- **Data Validation**: Pydantic
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions (Linting & Testing)

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- Google Cloud API Key (Gemini)
- (Optional) Ayrshare API Key for real posting

