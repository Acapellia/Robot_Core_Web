# Test Sender Server

간단한 WebSocket 송신 서버입니다. 서버를 실행하면 포트를 열어 클라이언트 연결을 기다리고, 운영자가 템플릿을 선택해 등록된 JSON 메시지를 연결된 클라이언트들에게 전송합니다.

설치 및 실행:

```bash
cd "99. Test Sender Server"
python3 -m pip install -r requirements.txt
python3 sender.py --host 0.0.0.0 --port 8080
```

명령어:
- `list` : 템플릿 목록 표시
- `clients` : 연결된 클라이언트 수 표시
- `번호` : 템플릿 인덱스로 메시지 생성/전송
- `quit` : 종료

템플릿은 `templates.json`에 정의되어 있습니다. 필요하면 템플릿을 수정해 주세요.
