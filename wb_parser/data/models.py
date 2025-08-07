from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PriceHistory:
    product_id: int
    timestamp: str
    price: int
    old_price: Optional[int]
    discount: Optional[int]

@dataclass
class Product:
    id: Optional[int]  # Для ID из базы данных
    timestamp: str
    brand: str
    name: str
    rate: float
    count_evolutions: int
    price: int
    old_price: Optional[int]
    discount: Optional[int]
    link: str
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id"),
            timestamp=data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            brand=data.get("brand", ""),
            name=data.get("name", ""),
            rate=float(data.get("rate", 0)),
            count_evolutions=int(data.get("count_evolutions", 0)),
            price=int(data.get("price", 0)),
            old_price=int(data.get("old_price", 0)) if data.get("old_price") else None,
            discount=int(data.get("discount", 0)) if data.get("discount") else None,
            link=data.get("link", "")
        )
