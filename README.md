# 🎓 UNIVPILOT — University Management (Students & Staff)

> Django project for the exam: a university management web app with authentication, role hierarchy, activity history, scope-limited CRUD, and printable reports.

---

## 📋 Roles & Permission Matrix

| Role | Scope | Can do |
|---|---|---|
| 🛡️ System Administrator | Global (technical) | Manage all accounts, configure the app, view all history |
| 🎯 Academic Director | Whole university | Cross-faculty views and reports |
| 🏛️ Dean | One faculty | Manage departments, programs, and courses of their faculty |
| 📂 Department Head | One department | Manage courses, students, and enrollments of their department |
| 📚 Professor | Their courses | Enter/modify grades for students enrolled in their courses only |
| 📝 Secretary | One department | Manage student files and enrollments, no grade access |
| 🧑‍🎓 Student | Themselves | View their profile, grades, average, and honors |

> **Principle**: Each role only sees and modifies their own scope (establishment > faculty > department > course), never everything by default. Implemented via Django groups (`configurer_roles`) + queryset filtering on the `Utilisateur` model (`departements_geres()`, `a_acces_global`).

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Authentication** | + "My Profile" page self-service for all roles (personal info, password change, read-only scope) |
| 📜 **Activity History** | Automatic via Django signals, viewable by admin & academic director |
| 🔄 **Scoped CRUD** | Faculties (global), departments/programs/courses (dean/head), students/enrollments (head/secretary), grades (professor only) |
| 🧮 **Business Logic** | Average/honors calculation, at-risk detection (avg < 10), course capacity check |
| 🖨️ **Printable Reports** | Student grade report, student list, staff list, course performance (avg + distribution) |
| 📊 **Role Dashboards** | Single entry point, content changes entirely by role |
| 🎨 **Academic Identity** | Oxford blue + gold, Fraunces (titles) / Work Sans (interface), card grids, dense tables |

---

## 🚀 Local Installation (SQLite, default)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Initialize database & demo data
python manage.py migrate
python manage.py donnees_demo   # creates role groups + demo accounts + realistic data

# Run the server
python manage.py runserver
```

🌐 **Go to** http://127.0.0.1:8000/

---

## 👥 Demo Accounts

| Role | Username | Password |
|---|---|---|
| 🛡️ System Administrator | `admin` | `AdminUniv2026!` |
| 🎯 Academic Director | `directeur` | `Directeur2026!` |
| 🏛️ Dean (Faculty of Science) | `doyen` | `Doyen2026!` |
| 📂 Department Head (CS) | `chef_dept` | `ChefDept2026!` |
| 📚 Professor (CS) | `professeur` | `Prof2026!` |
| 📝 Secretary (CS) | `secretaire` | `Secretaire2026!` |
| 🧑‍🎓 Student | `etudiant1` | `Etudiant2026!` |

> ⚠️ **These passwords are weak on purpose. Change them before any real deployment.**

---

## 🗄️ Using MySQL via XAMPP (instead of SQLite)

1. 🚀 Start **Apache** and **MySQL** from the XAMPP control panel.
2. 🌐 Open phpMyAdmin (http://localhost/phpmyadmin) and create a database `gestion_universite` (utf8mb4_unicode_ci).
3. 📝 In `.env`, set:
   ```env
   USE_MYSQL=True
   MYSQL_DATABASE=gestion_universite
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   ```
4. 🔄 Re-run `python manage.py migrate` then `python manage.py donnees_demo`.

> 💡 **Note**: PyMySQL is used as the MySQLdb driver in `settings.py` — mysqlclient was skipped due to native compilation issues on some systems.

---

## 📁 Project Structure

```
universite/     # 🧠 Global Django settings and routes
comptes/        # 👤 Users, roles, login, profile, activity history
academique/     # 🏛️ Faculties, departments, programs, courses, academic years
etudiants/      # 🧑‍🎓 Student records, enrollments, grades, professor grade entry
rapports/       # 🖨️ Printable reports (transcripts, lists, course performance)
templates/      # 🎨 Shared base template (base.html) + pagination
```

---

## 📜 Git History

The project was built step by step, each step as a separate commit (`git log --oneline` for details):

```
scaffold → DB config → user/roles model → academic structure → students/grades
→ migrations → permissions → auth/profile/dashboards → academic CRUD
→ student/grade CRUD → reports → demo data → redirect bug fix
```

> 🔧 **Note**: Last commit fixed a redirect bug found while testing unauthorized access.

---

## 🚧 What's Missing / Could Be Improved

- 📄 PDF export for reports (e.g. `weasyprint`) in addition to browser printing
- 🔔 Notifications for students dropping below the passing threshold
- 🧪 Automated tests (`python manage.py test`) to lock down the scope filtering behavior

---

## 📄 License

MIT — feel free to use, modify, and distribute. See [LICENSE](LICENSE) for details.

---

*Made with ☕ and Django — for educational purposes.*
