"""
Configuration file - הגדרות מרכזיות למערכת
"""
import os
from dotenv import load_dotenv
from crewai import LLM

# Load environment variables
load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in .env file")

# Claude LLM - משותף לכל הסוכנים
claude_llm = LLM(
    model="anthropic/claude-sonnet-4-5-20250929",
    api_key=ANTHROPIC_API_KEY
)

# System Configuration
VERBOSE = True
MAX_ITERATIONS = 10
DEFAULT_TEMPERATURE = 0.7

# Paths
DATA_PATH = "data"
KNOWLEDGE_BASE_PATH = os.path.join(DATA_PATH, "knowledge_base")
FEEDBACK_HISTORY_PATH = os.path.join(DATA_PATH, "feedback_history")
CONVERSATION_HISTORY_PATH = os.path.join(DATA_PATH, "conversation_history")

# Agent Configuration
AGENT_CONFIG = {
    "allow_delegation": True,
    "verbose": VERBOSE,
    "max_iter": MAX_ITERATIONS
}

# Process Configuration
PROCESS_TYPE = "hierarchical"  # או "sequential"
