import sys
import pathlib
import asyncio

# 프로젝트 루트를 sys.path에 추가하여 'src' 패키지를 찾을 수 있게 함
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.UpstreamManager.http_auth_ws import HttpAuthWebSocketConnection

async def main():
    auth_url = "http://127.0.0.1:8080/users/login"
    user_id = "admin"
    password = "pass0001!"
    # 서버가 기대하는 POST 바디 구조
    login_payload = {"id": user_id, "pw": password, "keepAliveTimeOut": 900}

    def ws_factory(token: str) -> str:
        # 요청 정보들을 쿼리 파라미터로 조합
        # 요청 예시: /?api-key=<token>&ch=0,1,2,3&hubMeta
        from urllib.parse import quote_plus
        parts = [f"api-key={quote_plus(token)}", "ch=0,1,2,3", "hubMeta"]
        query = "&".join(parts)
        return f"ws://127.0.0.1:8080/?{query}"

    inbound = asyncio.Queue()

    async def on_connect(conn):
        # auth_token은 HttpAuthWebSocketConnection에서 설정됩니다
        print("Connected. API key:", getattr(conn, 'auth_token', None))
        # 디버그: 실제 사용된 WS URI
        print("WS URI used:", getattr(conn, 'ws_uri_used', None))
        # 디버그: 응답 헤더 출력 가능하면 출력
        try:
            proto = getattr(conn, '_ws', None)
            if proto is not None and hasattr(proto, 'response_headers'):
                print("Handshake response headers:", proto.response_headers)
        except Exception as e:
            print("헤더 출력 중 에러:", e)
        # 연결 후에는 inbound 큐로 메시지가 들어옵니다. 수신은 메인 루프에서 처리합니다.

    conn = HttpAuthWebSocketConnection(
        auth_url=auth_url,
        ws_uri_factory=ws_factory,
        login_payload=login_payload,
        # 서버의 va-metadata 핸들러로 라우팅되도록 서브프로토콜 요청
        subprotocols=["va-metadata"],
        name="example_http_conn",
        inbound_queue=inbound,
        outbound_queue=None,
        on_connect=on_connect,
        retry_interval=5,
        max_retries=10,
    )

    # run_loop을 백그라운드 태스크로 실행하고 inbound 큐에서 메시지를 소비합니다
    task = asyncio.create_task(conn.run_loop())

    try:
        # 예시: 최대 20개 메시지 또는 30초 타임아웃 동안 수신
        for _ in range(20):
            try:
                source, raw = await asyncio.wait_for(inbound.get(), timeout=30)
                print(f"Received from {source}: {raw}")
                inbound.task_done()
            except asyncio.TimeoutError:
                print("수신 대기 타임아웃, 종료합니다.")
                break
    finally:
        conn.stop()
        await task

if __name__ == '__main__':
    asyncio.run(main())
