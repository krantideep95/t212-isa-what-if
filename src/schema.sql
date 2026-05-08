CREATE TABLE IF NOT EXISTS transactions (
    raw_id           TEXT PRIMARY KEY,
    source_file      TEXT NOT NULL,
    action           TEXT NOT NULL,
    ts               TEXT NOT NULL,
    date             TEXT NOT NULL,
    isin             TEXT,
    ticker           TEXT,
    name             TEXT,
    shares           REAL,
    price_native     REAL,
    ccy_native       TEXT,
    fx               REAL,
    total_gbp        REAL
);

CREATE INDEX IF NOT EXISTS idx_tx_date     ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_tx_action   ON transactions(action);
CREATE INDEX IF NOT EXISTS idx_tx_ticker   ON transactions(ticker);

CREATE TABLE IF NOT EXISTS prices (
    ticker     TEXT NOT NULL,
    date       TEXT NOT NULL,
    open_gbp   REAL NOT NULL,
    source     TEXT NOT NULL CHECK (source IN ('transaction','yfinance')),
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date);
