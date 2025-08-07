import sqlite3
from typing import List, Optional
from pathlib import Path
from data.models import Product, PriceHistory

class Database:
    def __init__(self, db_name: str = "output/wildberries.db"):
        self.db_name = db_name
        self._create_database()
    
    def _create_database(self):
        """Создает базу данных и таблицы, если они не существуют"""
        Path("output").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Таблица товаров
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    name TEXT NOT NULL,
                    rate REAL NOT NULL,
                    count_evolutions INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    old_price INTEGER,
                    discount INTEGER,
                    link TEXT NOT NULL,
                    UNIQUE(brand, name, link) ON CONFLICT IGNORE
                )
            """)
            
            # Таблица истории цен
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    old_price INTEGER,
                    discount INTEGER,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            # Индексы для ускорения поиска
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_link ON products(link)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp)")
            
            conn.commit()
    
    def save_products(self, products: List[Product]):
        """Сохраняет список товаров и их текущие цены в базу данных"""
        if not products:
            print("Нет данных для сохранения в базу данных")
            return
        
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                for product in products:
                    # Вставляем или получаем существующий товар
                    cursor.execute("""
                        INSERT OR IGNORE INTO products (
                            timestamp, brand, name, rate, 
                            count_evolutions, price, old_price, 
                            discount, link
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product.timestamp,
                        product.brand,
                        product.name,
                        product.rate,
                        product.count_evolutions,
                        product.price,
                        product.old_price,
                        product.discount,
                        product.link
                    ))
                    
                    # Получаем ID товара
                    cursor.execute("""
                        SELECT id FROM products WHERE link = ?
                    """, (product.link,))
                    product_id = cursor.fetchone()[0]
                    
                    # Сохраняем историю цен
                    cursor.execute("""
                        INSERT INTO price_history (
                            product_id, timestamp, price, 
                            old_price, discount
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        product_id,
                        product.timestamp,
                        product.price,
                        product.old_price,
                        product.discount
                    ))
                
                conn.commit()
                print(f"\nУспешно сохранено {len(products)} товаров и их цен в базу данных {self.db_name}")
        
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении в базу данных: {e}")
    
    def get_price_history(self, product_link: str, days: int = 30) -> List[PriceHistory]:
        """Получает историю цен для конкретного товара"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT ph.* FROM price_history ph
                    JOIN products p ON ph.product_id = p.id
                    WHERE p.link = ? 
                    AND date(ph.timestamp) >= date('now', ?)
                    ORDER BY ph.timestamp DESC
                """, (product_link, f"-{days} days"))
                
                return [
                    PriceHistory(
                        product_id=row[1],
                        timestamp=row[2],
                        price=row[3],
                        old_price=row[4],
                        discount=row[5]
                    ) for row in cursor.fetchall()
                ]
        
        except sqlite3.Error as e:
            print(f"Ошибка при получении истории цен: {e}")
            return []
    
    def get_price_changes(self, days: int = 7) -> List[dict]:
        """Возвращает товары с наибольшими изменениями цен"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        p.id, p.brand, p.name, p.link,
                        ph1.price AS current_price,
                        ph2.price AS previous_price,
                        ((ph1.price - ph2.price) * 100.0 / ph2.price) AS change_percent
                    FROM products p
                    JOIN price_history ph1 ON p.id = ph1.product_id
                    JOIN price_history ph2 ON p.id = ph2.product_id
                    WHERE ph1.timestamp = (
                        SELECT MAX(timestamp) FROM price_history WHERE product_id = p.id
                    )
                    AND ph2.timestamp = (
                        SELECT MAX(timestamp) FROM price_history 
                        WHERE product_id = p.id AND timestamp < ph1.timestamp
                        AND date(timestamp) >= date('now', ?)
                    )
                    ORDER BY ABS(change_percent) DESC
                    LIMIT 20
                """, (f"-{days} days",))
                
                return [
                    {
                        "id": row[0],
                        "brand": row[1],
                        "name": row[2],
                        "link": row[3],
                        "current_price": row[4],
                        "previous_price": row[5],
                        "change_percent": round(row[6], 2)
                    } for row in cursor.fetchall()
                ]
        
        except sqlite3.Error as e:
            print(f"Ошибка при анализе изменения цен: {e}")
            return []
        
    def get_product_by_link(self, link: str) -> Optional[Product]:
        """Получает товар по ссылке"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM products WHERE link = ?
                """, (link,))
                row = cursor.fetchone()
                
                if row:
                    return Product(
                        id=row[0],
                        timestamp=row[1],
                        brand=row[2],
                        name=row[3],
                        rate=row[4],
                        count_evolutions=row[5],
                        price=row[6],
                        old_price=row[7],
                        discount=row[8],
                        link=row[9]
                    )
                return None
        except sqlite3.Error as e:
            print(f"Error getting product: {e}")
            return None
