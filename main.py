import flet as ft
import sqlite3
import hashlib
import os
from datetime import datetime

APP_NAME = "ZEE PAY"
DB_PATH = os.path.join(os.path.dirname(__file__), "zee_pay.db")
GREEN = "#078B50"
DARK_GREEN = "#056B3D"
LIGHT_BG = "#F3F7F4"
TEXT = "#17231D"
MUTED = "#718078"
RED = "#D93636"

def db_connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db_connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                pin_hash TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0,
                savings INTEGER NOT NULL DEFAULT 0
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                amount INTEGER NOT NULL,
                kind TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def pin_hash(pin):
    return hashlib.sha256(("zee-pay-demo:" + pin).encode("utf-8")).hexdigest()

def main(page: ft.Page):
    init_db()
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_BG
    page.padding = 0
    page.spacing = 0
    page.window_width = 420
    page.window_min_width = 320
    page.window_height = 850
    page.scroll = ft.ScrollMode.AUTO
    page.rtl = True

    state = {"phone": None}

    def toast(message):
        page.snack_bar = ft.SnackBar(content=ft.Text(message, text_align=ft.TextAlign.RIGHT))
        page.snack_bar.open = True
        page.update()

    def text(value, size=14, color=TEXT, bold=False):
        return ft.Text(value, size=size, color=color,
                       weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
                       text_align=ft.TextAlign.RIGHT)

    def button(label, on_click, icon=None, primary=False):
        return ft.ElevatedButton(
            text=label, on_click=on_click, icon=icon,
            bgcolor=GREEN if primary else "#FFFFFF",
            color="#FFFFFF" if primary else GREEN,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=13),
                padding=14,
                elevation=0
            ),
            expand=True
        )

    def field(label, password=False, keyboard=None, hint=None):
        return ft.TextField(
            label=label, password=password, can_reveal_password=password,
            keyboard_type=keyboard, hint_text=hint,
            text_align=ft.TextAlign.RIGHT,
            border_radius=12, filled=True, bgcolor="#FFFFFF",
            border_color="#DCE7DF", focused_border_color=GREEN
        )

    def header():
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=18),
            bgcolor="#FFFFFF",
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(spacing=8, controls=[
                        ft.Image(
    src="assets/zee_logo.png",
    width=42,
    height=42,
    fit=ft.ImageFit.CONTAIN,
),
                        ft.Column(spacing=0, controls=[
                            ft.Text("ZEE PAY", size=22, weight=ft.FontWeight.BOLD, color=GREEN),
                            ft.Text("زي باي", size=12, color=MUTED)
                        ])
                    ]),
                    ft.IconButton(ft.Icons.NOTIFICATIONS_OUTLINED, icon_color=GREEN,
                                  tooltip="الإشعارات", on_click=lambda e: toast("لا توجد إشعارات جديدة"))
                ]
            )
        )

    def card(title, amount, subtitle, icon):
        return ft.Container(
            padding=20, border_radius=20, bgcolor=GREEN,
            content=ft.Column(spacing=10, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    text(title, 15, "#E7FFF0", True),
                    ft.Icon(icon, color="#FFFFFF", size=28)
                ]),
                ft.Text(amount, size=30, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                ft.Divider(color="#55B889", height=1),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    text(subtitle, 13, "#E7FFF0"),
                    ft.Icon(ft.Icons.SAVINGS_OUTLINED, color="#F4E58B")
                ])
            ])
        )

    def action_tile(label, icon, handler):
        return ft.Container(
            expand=True, padding=14, border_radius=17,
            bgcolor="#FFFFFF", border=ft.border.all(1, "#E1EAE4"),
            on_click=handler, ink=True,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(icon, color=GREEN, size=31),
                    ft.Text(label, size=14, color=TEXT, weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER)
                ]
            )
        )

    def get_user():
        with db_connect() as con:
            return con.execute("SELECT * FROM users WHERE phone=?",
                               (state["phone"],)).fetchone()

    def record(sender, receiver, amount, kind):
        with db_connect() as con:
            con.execute(
                "INSERT INTO transactions(sender,receiver,amount,kind,created_at) VALUES(?,?,?,?,?)",
                (sender, receiver, amount, kind, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )

    def home(e=None):
        page.controls.clear()
        user = get_user()
        if not user:
            login_screen()
            return

        recent = []
        with db_connect() as con:
            recent = con.execute(
                """SELECT * FROM transactions
                   WHERE sender=? OR receiver=?
                   ORDER BY id DESC LIMIT 4""",
                (state["phone"], state["phone"])
            ).fetchall()

        rows = []
        for tx in recent:
            incoming = tx["receiver"] == state["phone"] and tx["sender"] != state["phone"]
            sign = "+" if incoming else "-"
            color = GREEN if incoming else RED
            label = {
                "DEMO_DEPOSIT": "إيداع تجريبي",
                "TRANSFER": "تحويل أموال",
                "SAVING": "إضافة إلى الادخار",
                "SAVING_WITHDRAW": "سحب من الادخار"
            }.get(tx["kind"], tx["kind"])
            rows.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=11, horizontal=5),
                    content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Column(spacing=3, controls=[
                            text(label, 14, TEXT, True),
                            text(tx["created_at"], 11, MUTED)
                        ]),
                        ft.Text(f"{sign}{tx['amount']:,} SDG", color=color,
                                size=14, weight=ft.FontWeight.BOLD)
                    ])
                )
            )

        if not rows:
            rows = [ft.Container(padding=15, content=text("لا توجد عمليات حتى الآن", 13, MUTED))]

        page.add(
            header(),
            ft.Container(
                padding=18,
                content=ft.Column(spacing=16, controls=[
                    text("مرحباً بك في محفظتك", 18, TEXT, True),
                    card("رصيد المحفظة", f"{user['balance']:,} SDG",
                         f"المدخرات: {user['savings']:,} SDG", ft.Icons.ACCOUNT_BALANCE_WALLET),
                    text("الخدمات", 18, TEXT, True),
                    ft.Row(spacing=10, controls=[
                        action_tile("إرسال أموال", ft.Icons.SEND_ROUNDED, transfer_screen),
                        action_tile("استقبال الأموال", ft.Icons.DOWNLOAD_ROUNDED, receive_screen)
                    ]),
                    ft.Row(spacing=10, controls=[
                        action_tile("الادخار", ft.Icons.SAVINGS_OUTLINED, savings_screen),
                        action_tile("سحب من الادخار", ft.Icons.ACCOUNT_BALANCE, withdraw_savings_screen)
                    ]),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        text("آخر العمليات", 18, TEXT, True),
                        ft.TextButton("عرض الكل", on_click=history_screen)
                    ]),
                    ft.Container(
                        bgcolor="#FFFFFF", border_radius=16, padding=14,
                        content=ft.Column(spacing=2, controls=rows)
                    ),
                    ft.Row(controls=[
                        button("حسابي", profile_screen, ft.Icons.PERSON_OUTLINE),
                        button("تسجيل الخروج", logout, ft.Icons.LOGOUT)
                    ])
                ])
            )
        )
        page.update()

    def login_screen(e=None):
        page.controls.clear()
        phone = field("رقم الهاتف السوداني", hint="مثال: 249XXXXXXXXX",
                      keyboard=ft.KeyboardType.PHONE)
        pin = field("رمز PIN", password=True, keyboard=ft.KeyboardType.NUMBER)

        def login(e):
            with db_connect() as con:
                row = con.execute("SELECT phone FROM users WHERE phone=? AND pin_hash=?",
                                  (phone.value.strip(), pin_hash(pin.value.strip()))).fetchone()
            if row:
                state["phone"] = row["phone"]
                home()
            else:
                toast("رقم الهاتف أو رمز PIN غير صحيح")

        def register(e):
            p, code = phone.value.strip(), pin.value.strip()
            if len(p) < 8 or len(code) < 4:
                toast("أدخل رقم هاتف صحيحاً ورمز PIN من 4 أرقام على الأقل")
                return
            try:
                with db_connect() as con:
                    con.execute("INSERT INTO users(phone,pin_hash) VALUES(?,?)",
                                (p, pin_hash(code)))
                toast("تم إنشاء الحساب التجريبي. سجل الدخول الآن.")
            except sqlite3.IntegrityError:
                toast("رقم الهاتف مسجل مسبقاً")

        page.add(
            ft.Container(expand=True, alignment=ft.alignment.center,
                padding=24,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    controls=[ft.Image(
    src="assets/zee_logo.png",
    width=78,
    height=78,
    fit=ft.ImageFit.CONTAIN,
),
                                                     weight=ft.FontWeight.BOLD)),
                        ft.Text("ZEE PAY", size=32, color=GREEN, weight=ft.FontWeight.BOLD),
                        text("محفظتك الرقمية في السودان", 15, MUTED),
                        phone, pin,
                        button("تسجيل الدخول", login, ft.Icons.LOGIN, True),
                        button("إنشاء حساب جديد", register, ft.Icons.PERSON_ADD_ALT_1),
                        text("نسخة تجريبية — لا تستخدم أموالاً حقيقية", 11, RED)
                    ]
                )
            )
        )
        page.update()

    def form_screen(title, controls):
        page.controls.clear()
        page.add(
            header(),
            ft.Container(padding=20, content=ft.Column(spacing=15, controls=[
                ft.Text(title, size=23, color=TEXT, weight=ft.FontWeight.BOLD),
                *controls,
                button("رجوع للرئيسية", home, ft.Icons.ARROW_BACK)
            ]))
        )
        page.update()

    def transfer_screen(e=None):
        receiver = field("رقم هاتف المستلم", keyboard=ft.KeyboardType.PHONE)
        amount = field("المبلغ بالجنيه السوداني", keyboard=ft.KeyboardType.NUMBER)

        def send(e):
            try:
                value = int(amount.value)
                target_phone = receiver.value.strip()
                if value <= 0 or target_phone == state["phone"]:
                    raise ValueError
                with db_connect() as con:
                    con.execute("BEGIN IMMEDIATE")
                    sender = con.execute("SELECT balance FROM users WHERE phone=?",
                                         (state["phone"],)).fetchone()
                    target = con.execute("SELECT id FROM users WHERE phone=?",
                                         (target_phone,)).fetchone()
                    if not target:
                        toast("المستلم غير مسجل في ZEE PAY")
                        return
                    if sender["balance"] < value:
                        toast("رصيدك غير كافٍ")
                        return
                    con.execute("UPDATE users SET balance=balance-? WHERE phone=?",
                                (value, state["phone"]))
                    con.execute("UPDATE users SET balance=balance+? WHERE phone=?",
                                (value, target_phone))
                    con.execute(
                        "INSERT INTO transactions(sender,receiver,amount,kind,created_at) VALUES(?,?,?,?,?)",
                        (state["phone"], target_phone, value, "TRANSFER",
                         datetime.now().strftime("%Y-%m-%d %H:%M"))
                    )
                toast("تم التحويل التجريبي بنجاح")
                home()
            except (ValueError, TypeError):
                toast("أدخل مبلغاً صحيحاً ورقم المستلم")

        form_screen("إرسال الأموال", [
            receiver, amount,
            button("تأكيد التحويل التجريبي", send, ft.Icons.SEND, True)
        ])

    def receive_screen(e=None):
        form_screen("استقبال الأموال", [
            text("رقم محفظتك:", 14, MUTED),
            ft.Text(state["phone"], size=20, color=GREEN, weight=ft.FontWeight.BOLD),
            text("شارك رقم هاتفك مع الشخص الذي يريد إرسال الأموال إليك.", 14, TEXT)
        ])

    def savings_screen(e=None):
        amount = field("المبلغ المراد ادخاره", keyboard=ft.KeyboardType.NUMBER)

        def save(e):
            try:
                value = int(amount.value)
                if value <= 0:
                    raise ValueError
                with db_connect() as con:
                    con.execute("BEGIN IMMEDIATE")
                    user = con.execute("SELECT balance FROM users WHERE phone=?",
                                       (state["phone"],)).fetchone()
                    if user["balance"] < value:
                        toast("رصيدك غير كافٍ")
                        return
                    con.execute("UPDATE users SET balance=balance-?, savings=savings+? WHERE phone=?",
                                (value, value, state["phone"]))
                    con.execute(
                        "INSERT INTO transactions(sender,receiver,amount,kind,created_at) VALUES(?,?,?,?,?)",
                        (state["phone"], state["phone"], value, "SAVING",
                         datetime.now().strftime("%Y-%m-%d %H:%M"))
                    )
                toast("تمت إضافة المبلغ إلى الادخار")
                home()
            except (ValueError, TypeError):
                toast("أدخل مبلغاً صحيحاً")

        form_screen("الادخار", [amount, button("تأكيد الادخار", save, ft.Icons.SAVINGS, True)])

    def withdraw_savings_screen(e=None):
        amount = field("المبلغ المراد سحبه", keyboard=ft.KeyboardType.NUMBER)

        def withdraw(e):
            try:
                value = int(amount.value)
                if value <= 0:
                    raise ValueError
                with db_connect() as con:
                    con.execute("BEGIN IMMEDIATE")
                    user = con.execute("SELECT savings FROM users WHERE phone=?",
                                       (state["phone"],)).fetchone()
                    if user["savings"] < value:
                        toast("رصيد الادخار غير كافٍ")
                        return
                    con.execute("UPDATE users SET savings=savings-?, balance=balance+? WHERE phone=?",
                                (value, value, state["phone"]))
                    con.execute(
                        "INSERT INTO transactions(sender,receiver,amount,kind,created_at) VALUES(?,?,?,?,?)",
                        (state["phone"], state["phone"], value, "SAVING_WITHDRAW",
                         datetime.now().strftime("%Y-%m-%d %H:%M"))
                    )
                toast("تم السحب من الادخار")
                home()
            except (ValueError, TypeError):
                toast("أدخل مبلغاً صحيحاً")

        form_screen("سحب من الادخار", [
            amount, button("تأكيد السحب", withdraw, ft.Icons.ACCOUNT_BALANCE, True)
        ])

    def history_screen(e=None):
        with db_connect() as con:
            txs = con.execute(
                "SELECT * FROM transactions WHERE sender=? OR receiver=? ORDER BY id DESC",
                (state["phone"], state["phone"])
            ).fetchall()
        items = []
        for tx in txs:
            incoming = tx["receiver"] == state["phone"] and tx["sender"] != state["phone"]
            label = {
                "DEMO_DEPOSIT": "إيداع تجريبي",
                "TRANSFER": "تحويل أموال",
                "SAVING": "ادخار",
                "SAVING_WITHDRAW": "سحب من الادخار"
            }.get(tx["kind"], tx["kind"])
            items.append(ft.ListTile(
                title=text(label, 14, TEXT, True),
                subtitle=text(tx["created_at"], 11, MUTED),
                trailing=ft.Text(
                    ("+" if incoming else "-") + f"{tx['amount']:,} SDG",
                    color=GREEN if incoming else RED,
                    weight=ft.FontWeight.BOLD
                )
            ))
        if not items:
            items = [text("لا توجد عمليات مسجلة", 14, MUTED)]
        form_screen("سجل العمليات", [ft.Container(
            bgcolor="#FFFFFF", border_radius=15, padding=8,
            content=ft.Column(controls=items, spacing=0)
        )])

    def profile_screen(e=None):
        user = get_user()
        form_screen("حسابي", [
            text("رقم الهاتف", 13, MUTED),
            ft.Text(user["phone"], size=18, color=GREEN, weight=ft.FontWeight.BOLD),
            text("العملة: الجنيه السوداني (SDG)", 14),
            text("نوع الحساب: تجريبي محلي", 14, RED)
        ])

    def logout(e=None):
        state["phone"] = None
        login_screen()

    login_screen()

if __name__ == "__main__":
    ft.app(target=main)
