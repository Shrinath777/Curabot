import requests
import time

print("Waiting for server...")
time.sleep(2)

print("Sending test message to chatbot...")
r = requests.post(
    'http://localhost:8000/chat',
    json={'message': 'I have a severe headache and stiff neck with fever'},
    headers={'Content-Type': 'application/json'},
    timeout=60
)

print('STATUS:', r.status_code)
d = r.json()
print('BOT REPLY:', d.get('message', 'NO REPLY')[:400])
print()

hyps = d.get('hypotheses', [])
if hyps:
    print('TOP HYPOTHESES:')
    for h in hyps[:3]:
        print('  -', h.get('name'), ':', h.get('confidence'), '%')
else:
    print('No hypotheses returned')

print()
print('AGENT THOUGHTS:')
for t in d.get('agent_thoughts', [])[:4]:
    print(' ', t.get('agent'), '-', t.get('thought'))
