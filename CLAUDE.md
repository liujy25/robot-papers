# Robot Papers

Current architecture and commands are documented in README.md.

- Python 3.11+ standard-library builder: scripts/build.py.
- Page template: includes/index.html; assets: statics/.
- Feed config: config.toml; keywords, followed authors, conferences: preferences.json.
- Run `python -m unittest discover -s tests -v` before changing feed logic.
- Never report cached data as a successful fetch. Do not deploy when every source fails.
- Keep paper metadata HTML-escaped and outbound paper links restricted to arxiv.org.
- Preserve native keyboard navigation; do not bind Tab to expanding papers.
