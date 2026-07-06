import re

with open('docs/DevelopmentRoadmap.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Revert Phase 3 title
text = text.replace('## Phase 3: Federated Learning Implementation (Milestones 13-22) ✅ COMPLETE', '## Phase 3: Federated Learning Implementation (Milestones 13-22)')

# Remove ✅ from Phase 3 milestones and their status lines
for i in range(13, 23):
    text = re.sub(rf'### Milestone {i}: (.*?) ✅', rf'### Milestone {i}: \1', text)
    text = re.sub(rf'\*   \*\*Status:\*\* ✅ DONE.*?\n', '', text)

with open('docs/DevelopmentRoadmap.md', 'w', encoding='utf-8') as f:
    f.write(text)
