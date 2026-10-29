"""Flask Web Application for the AI Research Agent."""

import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify

from src.agent import ResearchAgent
from src.config import config, AgentConfig
from src.models import ConfidenceLevel

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    """Renders the research dashboard."""
    example_queries = [
        "Compare the top 3 open-source vector databases for a startup building RAG products.",
        "Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning.",
        "Research the pros and cons of using a multi-agent architecture for customer support automation.",
        "Compare different approaches to adding memory in an AI support agent."
    ]
    return render_template("index.html", example_queries=example_queries)


@app.route("/api/research", methods=["POST"])
def run_research_api():
    """API endpoint to execute a research query."""
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    mock_mode = data.get("mock_mode", False)

    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400

    cfg = AgentConfig()
    if mock_mode:
        cfg.mock_mode = True

    agent = ResearchAgent(cfg=cfg)
    steps_log = []

    def on_step(phase, msg):
        steps_log.append({"phase": phase, "message": msg})

    report, plan, judge_eval, tracer = agent.run(query, on_step_callback=on_step)

    # Format response payload
    response_payload = {
        "report": report.model_dump(),
        "plan": plan.model_dump(),
        "judge": judge_eval.model_dump(),
        "trace_summary": tracer.export_summary(),
        "steps_log": steps_log
    }

    return jsonify(response_payload)


def start_server(host="127.0.0.1", port=5000, debug=False):
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    start_server(debug=True)
