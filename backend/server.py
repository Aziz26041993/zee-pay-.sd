
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import hashlib
import secrets
import os

app = FastAPI(title="ZEE PAY API")
security = HTTPBearer()

DB = os.path.join(os.path.dirname(__file__), "zee_pay_server.db")

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT UNIQUE,
            password TEXT,
            balance INTEGER DEFAULT 100000
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            amount INTEGER,
            created TEXT
        );
        """)

init_db()

class Register(BaseModel):
    password: str

class Login(BaseModel):
    account: str
    password: str

class Transfer(BaseModel):
    receiver: str
    amount: int

def hash_password(password):
    salt = "ZEE_PAY_DEMO_"
    return hashlib.sha256(
        (salt + password).encode()
    ).hexdigest()

def get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_hash = hashlib.sha256(
        credentials.credentials.encode()
    ).hexdigest()

    with connect() as con:
        session = con.execute(
            "SELECT user_id FROM sessions WHERE token=?",
            (token_hash,)
        ).fetchone()

        if not session:
            raise HTTPException(401, "Invalid login")

        user = con.execute(
            "SELECT * FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()

        if not user:
            raise HTTPException(401, "Account not found")

        return user

@app.get("/")
def home():
    return {
        "app": "ZEE PAY",
        "currency": "SDG",
        "status": "development"
    }

@app.post("/register")
def register(data: Register):
    if len(data.password) < 8:
        raise HTTPException(400, "Password must be 8 characters")

    with connect() as con:
        for _ in range(20):
            account = str(secrets.randbelow(9000000000) + 1000000000)
            try:
                con.execute(
                    "INSERT INTO users(account,password,balance) VALUES(?,?,?)",
                    (account, hash_password(data.password), 100000)
                )
                return {
                    "success": True,
                    "account": account,
                    "balance": 100000,
                    "currency": "SDG",
                    "note": "Demo balance only"
                }
            except sqlite3.IntegrityError:
                continue

    raise HTTPException(500, "Could not create account")

@app.post("/login")
def login(data: Login):
    with connect() as con:
        user = con.execute(
            "SELECT * FROM users WHERE account=? AND password=?",
            (data.account, hash_password(data.password))
        ).fetchone()

        if not user:
            raise HTTPException(401, "Wrong account or password")

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        con.execute(
            "INSERT INTO sessions(token,user_id) VALUES(?,?)",
            (token_hash, user["id"])
        )

        return {
            "success": True,
            "token": token,
            "account": user["account"]
        }

@app.get("/balance")
def balance(user=Depends(get_user)):
    return {
        "account": user["account"],
        "balance": user["balance"],
        "currency": "SDG"
    }

@app.post("/transfer")
def transfer(data: Transfer, user=Depends(get_user)):
    if data.amount <= 0:
        raise HTTPException(400, "Invalid amount")

    if data.receiver == user["account"]:
        raise HTTPException(400, "Cannot transfer to yourself")

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")

        sender = con.execute(
            "SELECT * FROM users WHERE id=?",
            (user["id"],)
        ).fetchone()

        receiver = con.execute(
            "SELECT * FROM users WHERE account=?",
            (data.receiver,)
        ).fetchone()

        if not receiver:
            raise HTTPException(404, "Receiver not found")

        if sender["balance"] < data.amount:
            raise HTTPException(400, "Insufficient balance")

        con.execute(
            "UPDATE users SET balance=balance-? WHERE id=?",
            (data.amount, sender["id"])
        )

        con.execute(
            "UPDATE users SET balance=balance+? WHERE id=?",
            (data.amount, receiver["id"])
        )

        con.execute(
            """INSERT INTO transactions
            (sender,receiver,amount,created)
            VALUES(?,?,?,?)""",
            (
                sender["account"],
                receiver["account"],
                data.amount,
                datetime.utcnow().isoformat()
            )
        )

    return {
        "success": True,
        "message": "Transfer completed",
        "amount": data.amount,
        "currency": "SDG"
    }

@app.get("/transactions")
def transactions(user=Depends(get_user)):
    with connect() as con:
        rows = con.execute(
            """SELECT * FROM transactions
            WHERE sender=? OR receiver=?
            ORDER BY id DESC""",
            (user["account"], user["account"])
        ).fetchall()

        return [dict(row) for row in rows]

@app.get("/health")
def health():
    return {"status": "ok", "server": "ZEE PAY"}
