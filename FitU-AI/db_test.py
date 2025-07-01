import pymysql

# 접속 정보 설정
host = 'fitu-database.chy0qwwwof2j.ap-northeast-2.rds.amazonaws.com'
port = 3306
user = 'admin'  # 일반적으로 'admin', 정확한 사용자명은 확인 필요
password = 'your_password_here'  # 👉 동료에게 받은 비밀번호
database = 'your_database_name'  # 👉 사용할 DB 이름

try:
    # 연결 시도
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    print("✅ RDS 접속 성공!")

    with connection.cursor() as cursor:
        # 테이블 목록 확인
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("📦 테이블 목록:")
        for table in tables:
            print(table)

except Exception as e:
    print("❌ 접속 실패:", e)

finally:
    if 'connection' in locals() and connection.open:
        connection.close()
