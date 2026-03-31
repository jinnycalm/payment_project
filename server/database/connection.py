from sshtunnel import SSHTunnelForwarder
import psycopg2
from server.config import settings
from contextlib import contextmanager

# DB class
class RemoteDBConnection:
    def __init__(self, config):
        self.config = config
        self.tunnel = None
        self.connection = None

    def __enter__(self):
        '''SSH Tunnel 생성 및 DB 연결'''
        try:
            self.tunnel = SSHTunnelForwarder(
                (self.config.SSH_HOST, self.config.SSH_PORT),
                ssh_username=self.config.SSH_USER,
                ssh_pkey=self.config.SSH_KEY_PATH,
                remote_bind_address=(self.config.RDS_HOST, self.config.RDS_PORT)
            )
            self.tunnel.start()

            self.connection = psycopg2.connect(
                host='127.0.0.1',
                port=self.tunnel.local_bind_port,
                user=self.config.RDS_USER,
                database=self.config.RDS_DB_NAME,
                password=self.config.RDS_PASSWORD,
            )
            return self.connection        # with 구문에서 사용할 connection 객체 반환

        except Exception as e:
            self.__exit__(None, None, None)
            print(f'SSH 터널 생성 실패 : {e}')
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):      # with 구문에서 에러 발생 시 정보를 담아 보내는 객체들
        '''DB 연결 종료 및 SSH Tunnel 종료'''
        if self.connection:
            self.connection.close()
        if self.tunnel:
            self.tunnel.stop()


@contextmanager     # 제너레이터가 with 구문에서 컨텍스트 매니저로 작동하도록 하는 데코레이터
def get_db_conn(): 
    '''새로운 DB 연결 생성 및 자동 종료'''
    try:
        with RemoteDBConnection(settings) as conn:
            yield conn                  # 제너레이터로 상태 유지 및 값을 순차적으로 반환
    except Exception as e:
        print(f'DB 연결 실패 : {e}')
        raise


# 테스트용
def call_benefits(conn, query):
    '''LLM이 생성한 query 실행'''
    with conn.cursor() as cur:
        cur.execute(query)

        results = [cur.fetchone() for _ in range(3)]
        return results