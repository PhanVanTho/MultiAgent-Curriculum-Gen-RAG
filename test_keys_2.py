import requests

keys = [
    'AIzaSyBQIM0ZLF6R6_pqvqsVsHohTlDV7XxryyA',
    'AIzaSyCgb2IiHeNdt2ODFMVWKYJjXrRS7JEu4_0',
    'AIzaSyBR6fCRdsjvBa1Bok8SWU0vcOI1KWQaCUY',
    'AIzaSyAZrHoy6qpCNpGCAZXtxUelLnOy06TDBog',
    'AIzaSyAGdwl-caJbEsk3_0pQl0HipC-ENlDSxA8'
]

for k in keys:
    res = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={k}",
        json={"contents":[{"parts":[{"text":"hi"}]}]}
    )
    print(f"Key {k[:10]}... Status: {res.status_code}")
    if res.status_code != 200:
        print(f"  Error: {res.json()}")
