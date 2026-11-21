# Spice Garden - Food Ordering Website with AI-Style Support Chatbot

A complete Django + SQLite food ordering website: menu with search and filters, session cart,
coupons, checkout, order tracking, cancellation, refunds, authentication, profile and address
management, Django admin, and a floating support chatbot.

## Project layout

    food_project/
    ├── manage.py
    ├── requirements.txt
    ├── build.sh              # build step used by hosting platforms
    ├── Procfile              # start command for gunicorn
    ├── config/               # settings, root URLs, WSGI
    ├── menu/                 # categories, food items, homepage, menu page, seed command
    ├── accounts/             # signup, profile, saved addresses
    ├── orders/               # cart, coupons, checkout, orders, payments, refunds
    ├── chatbot/              # chatbot engine, support tickets, chat history, tests
    ├── templates/            # HTML templates (base.html, home.html, ...)
    ├── static/               # CSS and JavaScript
    └── media/                # uploaded food images (created on first upload)

---

## PART 1 - Run the project on your computer

### Step 1: Install Python
Install Python 3.11 or newer from https://www.python.org/downloads/.
On Windows, tick **"Add python.exe to PATH"** during installation.

Check it works:

    python --version

(On macOS/Linux you may need `python3` instead of `python`.)

### Step 2: Extract the project
Unzip `food_project.zip` to a folder such as `Documents/food_project`.

Open a terminal inside the `food_project` folder (the one that contains `manage.py`).

### Step 3: Create and activate a virtual environment

Windows (PowerShell):

    python -m venv venv
    venv\Scripts\Activate.ps1

Windows (Command Prompt):

    python -m venv venv
    venv\Scripts\activate.bat

macOS / Linux:

    python3 -m venv venv
    source venv/bin/activate

You should now see `(venv)` at the start of your terminal line.

### Step 4: Install the dependencies

    pip install -r requirements.txt

### Step 5: Create the database tables

    python manage.py migrate

This creates `db.sqlite3` with all tables.

### Step 6: Load sample food, prices and coupons

    python manage.py seed_menu

You should see: `Sample menu and coupons are loaded.`

### Step 7: Create an admin account

    python manage.py createsuperuser

Enter a username, email (optional) and a password of at least 8 characters.

### Step 8: Start the server

    python manage.py runserver

Open these in your browser:

- Website: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

### Step 9: Test the main flow
1. Click **Sign up** and create a customer account.
2. Go to **Menu**, click **Add** on a few dishes.
3. Open **Cart**, try coupon `WELCOME10` or `FLAT50`.
4. Click **Proceed to checkout**, fill the form and place the order.
5. Open **My Orders** to see tracking, then try **Cancel order**.
6. Click the orange chat button at the bottom right and try:
   - `where my order`  (it will ask for your order ID)
   - `ordr not recived`
   - `refund not came`
   - `Tell me about Python programming.` (should be politely redirected)

### Step 10: Run the automated tests

    python manage.py test chatbot

All tests should print `OK`.

### Step 11: Change the order status (staff only)
Log in at `/admin/` with your superuser account, open **Orders**, and change the status
in the list (for example, Confirmed -> Preparing -> Out for Delivery -> Delivered).
Customers see the new status on their order page and the chatbot reports it.

---

## Common problems

| Problem | Fix |
|---|---|
| `python` not found | Use `python3` (macOS/Linux) or reinstall Python with PATH enabled. |
| `ModuleNotFoundError: No module named 'django'` | Activate the venv first (Step 3), then run `pip install -r requirements.txt`. |
| `ImageField` / Pillow error | Run `pip install Pillow`. |
| Page has no styling | You need internet access: Bootstrap loads from a CDN. |
| `no such table` | Run `python manage.py migrate`. |
| Menu is empty | Run `python manage.py seed_menu`. |
| Chatbot says "something went wrong" | Check the terminal for the traceback. Usually a missing migration: run `migrate` again. |
| Port 8000 busy | `python manage.py runserver 8001` |

---

## PART 2 - Publish the project online (free, step by step)

There are two simple options. **Option A (PythonAnywhere)** is the easiest for SQLite because
the database file stays on disk. **Option B (Render)** works well too, but requires a paid
disk for SQLite to persist between deploys.

Before publishing, generate a strong secret key. Run this in your terminal (inside the venv):

    python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"

Save the output. You will paste it as `DJANGO_SECRET_KEY` on the server.

### Option A: PythonAnywhere (free tier, recommended for beginners)

**A1. Create the code repository (optional but recommended).**
Create a free account on https://github.com, create a new repository, and upload the
project files (drag the folder contents into the GitHub web page). Do NOT upload `venv/`
or `db.sqlite3`; the `.gitignore` file already excludes them.

**A2. Create a PythonAnywhere account.**
Sign up at https://www.pythonanywhere.com (Beginner account is free). Your site address will be
`yourusername.pythonanywhere.com`.

**A3. Upload the code.**
- Go to the **Files** tab and upload `food_project.zip`.
- Open a **Bash console** (Consoles tab -> Bash) and run:

      unzip food_project.zip -d /home/yourusername/
      cd /home/yourusername/food_project

  (If you use GitHub instead: `git clone https://github.com/yourname/your-repo.git food_project`.)

**A4. Create a virtual environment and install packages.**

      mkvirtualenv --python=/usr/bin/python3.11 venv
      pip install -r requirements.txt

  (If Python 3.11 is not listed, pick any 3.11+ version shown in the dropdown and use that path.)

**A5. Set environment variables.**
PythonAnywhere does not read a `.env` file automatically, so add the variables to the
virtualenv activation script. In the Bash console run:

      nano ~/.virtualenvs/venv/bin/postactivate

  Add these lines at the bottom (replace the values):

      export DJANGO_SECRET_KEY='paste-your-generated-key-here'
      export DJANGO_DEBUG=0
      export DJANGO_ALLOWED_HOSTS='yourusername.pythonanywhere.com'
      export DJANGO_CSRF_TRUSTED_ORIGINS='https://yourusername.pythonanywhere.com'
      export ANTHROPIC_API_KEY=''

  Save with `Ctrl+O`, `Enter`, then `Ctrl+X`. Reload with `deactivate` then `workon venv`.

**A6. Build the database and static files.**

      cd /home/yourusername/food_project
      python manage.py collectstatic --noinput
      python manage.py migrate
      python manage.py seed_menu
      python manage.py createsuperuser

**A7. Create the web app.**
- Go to the **Web** tab -> **Add a new web app** -> **Manual configuration** -> pick the same Python version.
- In **Virtualenv**, enter: `/home/yourusername/.virtualenvs/venv`
- In **Code**, set **Source code** and **Working directory** to `/home/yourusername/food_project`.
- Click **WSGI configuration file** and replace its entire content with:

      import os
      import sys

      path = "/home/yourusername/food_project"
      if path not in sys.path:
          sys.path.insert(0, path)

      os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

      from django.core.wsgi import get_wsgi_application
      application = get_wsgi_application()

- Under **Static files**, add two entries:
  - URL `/static/` -> Directory `/home/yourusername/food_project/staticfiles`
  - URL `/media/` -> Directory `/home/yourusername/food_project/media`

- Click the green **Reload** button at the top of the Web tab.

**A8. Test your live site.**
Open `https://yourusername.pythonanywhere.com/`. Log in to `/admin/` with your superuser
account. Free PythonAnywhere accounts only allow outgoing connections to approved sites, so the
optional AI fallback may not work there. The rule-based chatbot works fully without it.

**A9. Updating later.** Upload new files, run `collectstatic` and `migrate` again if needed,
then press **Reload**.

### Option B: Render (free web service, with note on SQLite)

Render's free web service has an ephemeral disk: your SQLite data is erased on every redeploy
or restart. Use it for demos only. For real customers, use PythonAnywhere (Option A) or move the
project to PostgreSQL and a managed database.

**B1.** Push the project to GitHub (see A1).

**B2.** Go to https://render.com, sign in with GitHub, click **New +** -> **Web Service**, and pick your repository.

**B3.** Fill in the form:
- **Runtime:** Python 3
- **Build command:** `bash build.sh`
- **Start command:** `gunicorn config.wsgi --log-file -`

**B4.** Open **Environment** and add:

| Key | Value |
|---|---|
| `DJANGO_SECRET_KEY` | your generated key |
| `DJANGO_DEBUG` | `0` |
| `DJANGO_ALLOWED_HOSTS` | `your-service-name.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://your-service-name.onrender.com` |
| `PYTHON_VERSION` | `3.12.4` |

**B5.** Click **Create Web Service**. Wait for the build log to finish, then open your URL.

**B6.** Create the admin account from the Render **Shell** tab:

      python manage.py createsuperuser

---

## PART 3 - Before you go live (checklist)

- [ ] `DJANGO_DEBUG=0` and a long random `DJANGO_SECRET_KEY` are set.
- [ ] `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` contain your real domain.
- [ ] Update `RESTAURANT_NAME`, `RESTAURANT_ADDRESS`, `SUPPORT_EMAIL`, `SUPPORT_PHONE`,
      `RESTAURANT_HOURS` in `config/settings.py` to your real details.
- [ ] Replace the sample menu through the admin panel and upload real food photos
      (each food item has an Image field).
- [ ] Use a real payment gateway (Razorpay, Stripe, etc.) before accepting real online payments.
      The "Online Payment (demo)" option only simulates payment.
- [ ] Give your team access through `/admin/` by setting **Staff status** on their user accounts.

## Optional: turn on the AI chatbot fallback

The chatbot answers orders, menu, payments, refunds and support with built-in rules that use
your database. For unclear food-related questions it can also call the Anthropic API.

1. Get an API key from https://console.anthropic.com/.
2. Set the environment variable `ANTHROPIC_API_KEY` (see Part 2) and restart the server.

Without a key the chatbot still works and politely asks for clarification.

## Security notes

- Passwords are hashed by Django and checked against the built-in password validators.
- Order, cancellation and refund data are only visible to the owning customer.
- The chatbot blocks prompt-injection, SQL and code requests and never exposes other customers' data.
- All database access uses the Django ORM (no raw SQL).
- Forms use CSRF protection; the chatbot sends the CSRF token with every request.
