import re

def update_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'"timeout_seconds": \d+', '"timeout_seconds": 1200', content)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

update_file(r'C:\python\AgentHive\backend\app\agents\seeder.py')
update_file(r'C:\python\AgentHive\backend\seed_50_agents.py')
