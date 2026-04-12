import requests

with open('D:/Exercise-Correction/Exercise-Correction/test_out.mp4', 'rb') as f:
    resp = requests.post('http://127.0.0.1:8000/api/video/upload?type=bicep_curl', files={'file': ('test.mp4', f, 'video/mp4')})
    print(resp.status_code, resp.text)
