import pymysql

class User:
    def __init__(self, id, name, age):
        self.id = id
        self.name = name
        self.age = age
    
    def get_role(self):
        return "普通用户"
    
    def save_to_db(self):
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='@Sariel0901',
            database='student',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        sql = "INSERT INTO users (id, username, created_at) VALUES (%s, %s, NOW())"
        cursor.execute(sql, (self.id, self.name))
        conn.commit()
        conn.close()
        print(f"用户 {self.name} 已保存到数据库")

if __name__ == "__main__":
    u = User(1, "张三", 25)
    print(u.get_role())
    u.save_to_db()