from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

app = Flask(__name__)

# Database config (SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Database table
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.String(10), nullable=True)  # "YYYY-MM-DD"


def parse_due(due_str):
    """Convert 'YYYY-MM-DD' string -> date object (or None)."""
    if not due_str:
        return None
    try:
        return datetime.strptime(due_str, "%Y-%m-%d").date()
    except ValueError:
        return None


# ✅ Render fix: ensure tables exist before any request hits the DB
@app.before_first_request
def create_tables():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def home():
    # CREATE (Add task)
    if request.method == "POST":
        title = request.form["task"].strip()
        due = request.form.get("due_date", "").strip()

        if title:
            db.session.add(Task(title=title, due_date=due if due else None))
            db.session.commit()

        return redirect(url_for("home"))

    # READ (Filter tasks)
    filter_type = request.args.get("filter", "all")

    if filter_type == "active":
        tasks = Task.query.filter_by(done=False).order_by(Task.id.desc()).all()
    elif filter_type == "done":
        tasks = Task.query.filter_by(done=True).order_by(Task.id.desc()).all()
    else:
        tasks = Task.query.order_by(Task.id.desc()).all()

    # Counters
    total_tasks = Task.query.count()
    active_tasks = Task.query.filter_by(done=False).count()
    done_tasks = Task.query.filter_by(done=True).count()

    # Today for due date checks
    today = date.today()

    # Build view model for template (status per task)
    task_view = []
    for t in tasks:
        due_obj = parse_due(t.due_date)
        status = "none"  # none | today | overdue | future

        if due_obj:
            if due_obj < today and not t.done:
                status = "overdue"
            elif due_obj == today and not t.done:
                status = "today"
            else:
                status = "future"

        task_view.append({"task": t, "status": status})

    return render_template(
        "index.html",
        task_view=task_view,
        filter_type=filter_type,
        total_tasks=total_tasks,
        active_tasks=active_tasks,
        done_tasks=done_tasks,
        today=str(today),
    )


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    # UPDATE (Toggle done)
    filter_type = request.args.get("filter", "all")
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("home", filter=filter_type))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    # DELETE (Remove task)
    filter_type = request.args.get("filter", "all")
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("home", filter=filter_type))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    # UPDATE (Edit title + due date)
    filter_type = request.args.get("filter", "all")
    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        task.title = request.form["title"].strip()
        task.due_date = request.form.get("due_date", "").strip() or None
        db.session.commit()
        return redirect(url_for("home", filter=filter_type))

    return render_template("edit.html", task=task, filter_type=filter_type)


if __name__ == "__main__":
    # Local run
    app.run(host="0.0.0.0", port=10000)
