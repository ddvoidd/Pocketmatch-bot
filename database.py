import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    created_at TEXT NOT NULL
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    target_gender TEXT NOT NULL,
                    city TEXT NOT NULL,
                    bio TEXT,
                    interests TEXT,
                    photos TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    viewed BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (from_user_id) REFERENCES users (user_id),
                    FOREIGN KEY (to_user_id) REFERENCES users (user_id)
                )
            ''')

    def add_user(self, user_id, username, first_name, last_name=None):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, datetime.now().isoformat()))

    def user_exists(self, user_id):
        with self.get_connection() as conn:
            result = conn.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            return result.fetchone() is not None

    def create_profile(self, user_id, name, age, gender, target_gender, city, bio=""):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO profiles
                (user_id, name, age, gender, target_gender, city, bio, interests, photos, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, name, age, gender, target_gender, city, bio,
                '[]', '[]', datetime.now().isoformat()
            ))

    def get_profile(self, user_id):
        with self.get_connection() as conn:
            result = conn.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,))
            row = result.fetchone()

            if row:
                return {
                    'user_id': row['user_id'],
                    'name': row['name'],
                    'age': row['age'],
                    'gender': row['gender'],
                    'target_gender': row['target_gender'],
                    'city': row['city'],
                    'bio': row['bio'],
                    'interests': json.loads(row['interests']),
                    'photos': json.loads(row['photos']),
                    'is_active': bool(row['is_active']),
                    'updated_at': row['updated_at']
                }
            return None

    def profile_exists(self, user_id):
        return self.get_profile(user_id) is not None

    def add_photo_to_profile(self, user_id, photo_file_id):
        profile = self.get_profile(user_id)
        if profile:
            photos = profile['photos']
            if len(photos) < 1:
                photos.append(photo_file_id)
                with self.get_connection() as conn:
                    conn.execute(
                        'UPDATE profiles SET photos = ?, updated_at = ? WHERE user_id = ?',
                        (json.dumps(photos), datetime.now().isoformat(), user_id)
                    )
                return True
        return False

    def update_profile_field(self, user_id, field, value):
        allowed_fields = ['name', 'age', 'gender', 'target_gender', 'city', 'bio']
        if field not in allowed_fields:
            return False

        with self.get_connection() as conn:
            conn.execute(
                f'UPDATE profiles SET {field} = ?, updated_at = ? WHERE user_id = ?',
                (value, datetime.now().isoformat(), user_id)
            )
        return True

    def set_profile_active(self, user_id, is_active):
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE profiles SET is_active = ?, updated_at = ? WHERE user_id = ?',
                (is_active, datetime.now().isoformat(), user_id)
            )

    def find_profiles_for_user(self, current_user_id, limit=20):
        """Находит подходящие анкеты для пользователя ТОЛЬКО из его города"""
        current_profile = self.get_profile(current_user_id)
        if not current_profile or not current_profile['is_active']:
            return []

        with self.get_connection() as conn:
            target_condition = self._get_target_condition(current_profile['target_gender'])

            query = f'''
                SELECT p.*, u.username, u.first_name
                FROM profiles p
                JOIN users u ON u.user_id = p.user_id
                WHERE p.user_id != ?
                AND p.is_active = TRUE
                AND {target_condition}
                AND p.city = ?  -- ДОБАВЛЕНА ПРОВЕРКА ГОРОДА
                AND p.user_id NOT IN (
                    SELECT to_user_id FROM likes WHERE from_user_id = ?
                )
                ORDER BY p.updated_at DESC
                LIMIT ?
            '''

            result = conn.execute(query, (
                current_user_id,
                current_profile['city'],
                current_user_id,
                limit
            ))
            profiles = []

            for row in result:
                profiles.append({
                    'user_id': row['user_id'],
                    'username': row['username'],
                    'first_name': row['first_name'],
                    'name': row['name'],
                    'age': row['age'],
                    'gender': row['gender'],
                    'city': row['city'],
                    'bio': row['bio'],
                    'photos': json.loads(row['photos']),
                    'target_gender': row['target_gender']
                })

            return profiles

    def _get_target_condition(self, target_gender):
        """Возвращает SQL условие для поиска по полу"""
        conditions = {
            'male': "p.gender = 'male'",
            'female': "p.gender = 'female'",
            'all': "1=1"
        }
        return conditions.get(target_gender, "1=1")

    def add_like(self, from_user_id, to_user_id):
        """Добавляет лайк и возвращает True если это мэтч"""
        with self.get_connection() as conn:
            result = conn.execute('''
                SELECT 1 FROM likes
                WHERE from_user_id = ? AND to_user_id = ?
            ''', (from_user_id, to_user_id))

            if result.fetchone():
                return False

            conn.execute('''
                INSERT INTO likes (from_user_id, to_user_id, created_at)
                VALUES (?, ?, ?)
            ''', (from_user_id, to_user_id, datetime.now().isoformat()))

            result = conn.execute('''
                SELECT 1 FROM likes
                WHERE from_user_id = ? AND to_user_id = ?
            ''', (to_user_id, from_user_id))

            is_match = result.fetchone() is not None
            return is_match

    def get_match(self, user1_id, user2_id):
        """Проверяет есть ли мэтч между пользователями"""
        with self.get_connection() as conn:
            result = conn.execute('''
                SELECT 1 FROM likes
                WHERE (from_user_id = ? AND to_user_id = ?)
                AND (from_user_id = ? AND to_user_id = ?)
            ''', (user1_id, user2_id, user2_id, user1_id))

            is_match = result.fetchone() is not None
            print(f"🔍 DEBUG get_match: user1_id={user1_id}, user2_id={user2_id}, result={is_match}")
            return is_match

    def get_user_likes(self, user_id):
        """Получает лайки пользователя с информацией о username"""
        with self.get_connection() as conn:
            result = conn.execute('''
                SELECT l.*, u.first_name, u.username, p.name, p.age, p.photos
                FROM likes l
                JOIN users u ON u.user_id = l.to_user_id
                JOIN profiles p ON p.user_id = l.to_user_id
                WHERE l.from_user_id = ?
                ORDER BY l.created_at DESC
            ''', (user_id,))

            likes = []
            for row in result:
                likes.append({
                    'like_id': row['id'],
                    'to_user_id': row['to_user_id'],
                    'to_user_name': row['name'],
                    'to_user_age': row['age'],
                    'to_first_name': row['first_name'],
                    'to_username': row['username'],
                    'photos': json.loads(row['photos']),
                    'created_at': row['created_at']
                })
            return likes

    def get_unviewed_likes(self, user_id):
        """Получает непросмотренные лайки"""
        with self.get_connection() as conn:
            result = conn.execute('''
                SELECT l.*, u.first_name, u.username, p.name, p.age, p.photos
                FROM likes l
                JOIN users u ON u.user_id = l.from_user_id
                JOIN profiles p ON p.user_id = l.from_user_id
                WHERE l.to_user_id = ?
                AND l.viewed = 0
                ORDER BY l.created_at DESC
            ''', (user_id,))

            likes = []
            for row in result:
                likes.append({
                    'like_id': row['id'],
                    'from_user_id': row['from_user_id'],
                    'from_user_name': row['name'],
                    'from_user_age': row['age'],
                    'from_first_name': row['first_name'],
                    'from_username': row['username'],
                    'photos': json.loads(row['photos']),
                    'created_at': row['created_at']
                })
            return likes

    def mark_like_viewed(self, like_id):
        """Помечает лайк как просмотренный"""
        with self.get_connection() as conn:
            conn.execute('UPDATE likes SET viewed = 1 WHERE id = ?', (like_id,))

    def has_liked(self, from_user_id, to_user_id):
        """Проверяет, лайкал ли пользователь другого пользователя"""
        with self.get_connection() as conn:
            result = conn.execute('''
                SELECT 1 FROM likes
                WHERE from_user_id = ? AND to_user_id = ?
            ''', (from_user_id, to_user_id))
            return result.fetchone() is not None

    def clear_likes_history(self):
        """Очищает всю историю лайков (для ежедневного сброса)"""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM likes')
            logger.info("✅ История лайков очищена (ежедневный сброс)")
            return True