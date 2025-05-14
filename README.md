# Supply-chain-resilience-and-GenAI
Built an end-to-end AI system that detects and classifies real-time supply chain disruptions from global news articles. The goal is to enable Business Continuity Planning (BCP) by identifying threats early and assessing their impact on specific suppliers and the broader supply chain.
Web Scraping & Content Parsing: Collected news articles related to global events using Langchain + ChromiumLoader.

# Key Features
LLM-Based Event Classification: Used GPT-4 to classify events into categories like Geopolitical, Climate-related, Transport Disruptions, etc.
Supplier Mapping: Extracted supplier names and contextual location data from the news content.
Risk Profiling: Computed event-specific risk scores for each supplier using domain-based heuristics and AI inference.
Output: Structured Excel/JSON report mapping events to affected suppliers, with category, location, and impact rating.

# Tech Stack
Langchain + AsyncChromiumLoader
OpenAI GPT-4 API
Python (for orchestration and logic)
Pandas / Numpy (for data processing)
Excel Output / JSON API-ready format
