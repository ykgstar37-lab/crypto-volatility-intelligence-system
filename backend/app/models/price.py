import math

from sqlalchemy import Column, Date, Float, Integer, String, UniqueConstraint

from app.database import Base


class CoinDaily(Base):
    __tablename__ = "coin_daily"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uix_symbol_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)  # BTC, ETH, SOL
    date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Float)
    fng = Column(Integer)
    log_return = Column(Float)

    def compute_log_return(self, prev_close: float):
        if prev_close and prev_close > 0 and self.close and self.close > 0:
            self.log_return = math.log(self.close / prev_close)


# Backward compat alias
BtcDaily = CoinDaily
