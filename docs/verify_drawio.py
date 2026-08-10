#!/usr/bin/env python3
"""
Verification Script for AgentHive Draw.io Architecture Diagrams.
Parses docs/architecture.drawio with xml.etree.ElementTree to confirm valid XML schema structure
and checks for required architectural components.
"""

import sys
import os
import xml.etree.ElementTree as ET

def verify_drawio(file_path: str) -> bool:
    print(f"Verifying draw.io diagram file: {file_path}")
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return False

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as pe:
        print(f"ERROR: XML parsing failed for {file_path}: {pe}")
        return False

    # Check root tag
    if root.tag != "mxfile":
        print(f"ERROR: Invalid root element '{root.tag}'. Expected 'mxfile'.")
        return False

    # Check diagram tag
    diagram = root.find("diagram")
    if diagram is None:
        print("ERROR: Missing <diagram> element in mxfile.")
        return False

    # Check mxGraphModel
    graph_model = diagram.find("mxGraphModel")
    if graph_model is None:
        print("ERROR: Missing <mxGraphModel> element inside <diagram>.")
        return False

    # Check root model
    model_root = graph_model.find("root")
    if model_root is None:
        print("ERROR: Missing <root> element inside <mxGraphModel>.")
        return False

    # Collect mxCell IDs and values
    cells = model_root.findall("mxCell")
    cell_ids = {c.get("id") for c in cells if c.get("id")}
    cell_values = [c.get("value", "") for c in cells if c.get("value")]
    combined_text = " ".join(cell_values)

    # Basic root cells validation (0 and 1)
    if "0" not in cell_ids or "1" not in cell_ids:
        print("ERROR: Missing root mxCell IDs '0' or '1'.")
        return False

    print(f"XML Schema is VALID! Found {len(cells)} mxCell elements.")

    # Validate mandatory architectural concepts in combined text
    required_keywords = [
        "MultiAgentEngine",
        "generate_parallel",
        "/api/orchestrate",
        "Supervisor",
        "Swarm",
        "Router",
        "BaseAgent",
        "TOON",
        "ToolRegistry",
        "PostgreSQL",
        "Redis",
        "Celery",
        "Loki",
        "Prometheus",
        "Gemini",
        "Groq",
        "Ollama"
    ]

    missing = []
    for kw in required_keywords:
        if kw not in combined_text:
            missing.append(kw)

    if missing:
        print(f"WARNING: The following architectural keywords were not found in diagram: {missing}")
        return False

    print("ALL required architectural keywords verified in diagram text!")
    return True

def main():
    target_files = [
        os.path.join(os.path.dirname(__file__), "architecture.drawio"),
        os.path.join(os.path.dirname(__file__), "diagrams", "multi-agent-architecture.drawio")
    ]

    all_passed = True
    for fpath in target_files:
        if not verify_drawio(fpath):
            all_passed = False

    if all_passed:
        print("\nSUCCESS: All draw.io architecture diagrams passed XML schema & content verification!")
        sys.exit(0)
    else:
        print("\nFAILURE: Verification failed for one or more draw.io diagram files.")
        sys.exit(1)

if __name__ == "__main__":
    main()
