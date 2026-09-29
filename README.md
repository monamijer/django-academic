# 🗃️ GESTOCK — Web-based Stock Management Application

[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap%205-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](#)

> 🎓 Django (Python) project: web application with authentication, differentiated authorizations, activity history, CRUD operations on multiple types of items (products, categories, stock movements, users), search, and printable reports.

---

## ✨ Features

- 🔐 **Authentication**: login/logout (`comptes` app), accounts can be enabled/disabled.
- 🛡️ **Differentiated authorizations**:
  - 👑 Administrators (`est_administrateur=True`) → full permissions.
  - 👤 Other users → standard Django permissions assigned via **groups**
    (e.g. "Magasinier" group: can add/edit products and record movements,
    but cannot delete or manage accounts).
- 📜 **Activity history** (`JournalActivite`): every add, edit, view, delete,
  deactivation, search, login/logout and report printing is logged with the
  user, timestamp and related object — viewable in "Historique"
  (administrators only).
- 🔄 **Full CRUD** on:
  - 📦 Products (multiple categories/types), with enable/disable, search, low-stock alerts.
  - 🏷️ Product categories (with an associated color used throughout the UI).
  - 🔁 Stock movements (in/out), which automatically update quantities.
  - 👥 Users (administrators only), with group/role management.
- 🖨️ **Printable reports** (Print button → dedicated print layout):
  - 📊 In/out movements over a period (7 or 30 days, customizable).
  - ⏳ Expired and soon-to-expire products.
  - 📈 Current stock state with total value.
- 🎨 **Interface**: Bootstrap 5 + Bootstrap Icons, icon buttons, dedicated color
  per section (users = 🟣 purple, products = 🔵 blue, movements = 🟢 green, reports = 🟠 orange,
  destructive actions = 🔴 red), color badges per product category.
- 🌐 **Shared data**: all data (products, movements...) is visible to all logged-in
  users whose permissions allow it — not a per-user silo.

---

## 🚀 Local Installation

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit .env if needed

python manage.py migrate
python manage.py donnees_demo   # creates demo accounts and data
python manage.py runserver
```

🌍 Open http://127.0.0.1:8000/

### 🔑 Demo Accounts

| Role | Username | Password | Rights |
|------|----------|----------|--------|
| 👑 Administrator | `admin` | `AdminGestock2026!` | Full permissions |
| 📦 Magasinier | `magasinier` | `Magasin2026!` | Products/movements only, no delete, no user management |

> ⚠️ **Change these passwords before any real deployment.**

---

## 🐘 Using PostgreSQL (instead of SQLite)

1. 🛠️ Create a PostgreSQL database and user.
2. 📝 In `.env`, set:
   `DATABASE_URL=postgres://user:password@localhost:5432/gestock`
3. 🔄 Run `python manage.py migrate` again.

---

## 📁 Project Structure

```
gestock/        # ⚙️ Django project settings and global routes
comptes/        # 👥 users, login, groups/permissions, activity history
stock/          # 📦 categories, products, stock movements (CRUD, search)
rapports/       # 🖨️ printable reports (movements, expiry, stock state)
templates/      # 🧩 shared base template (base.html) + pagination
```

---

## 👑 Creating an Additional Administrator Account

```bash
python manage.py createsuperuser
```

Then, in the "Users" interface (or Django admin `/admin/`), check
"est_administrateur" to grant full permissions. ✅

---

## 🧭 Possible Next Steps

- 📄 Generate downloadable PDF reports (e.g. with `weasyprint`) in addition to browser printing.
- 📊 Add CSV/Excel export for lists.
- 🧪 Add automated tests (`python manage.py test`).

---

<div align="center">

**⭐ If you find this project useful, give it a star! ⭐**

Made with ❤️ using Django & Bootstrap

</div>
