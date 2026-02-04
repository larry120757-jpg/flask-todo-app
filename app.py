from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

app = Flask(__name__)

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ======================
# Database model
# ======================
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.String(10), nullable=True)  # YYYY-MM-DD


# ======================
# FORCE table creation
# (critical for Render)
# ======================
with app.app_context():
    db.create_all()


def parse_due(due_str):
    if not due_str:
        return None
    try:
        return datetime.strptime(due_str, "%Y-%m-%d").date()
    except ValueError:
        return None


@app.route("/", methods=["GET", "POST"])
def home():
    # CREATE
    if request.method == "POST":
        title = request.form["task"].strip()
        due = request.form.get("due_date", "").strip()

        if title:
            db.session.add(
                Task(
                    title=title,
                    due_date=due if due else None
                )
            )
            db.session.commit()

        return redirect(url_for("home"))

    # FILTER
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

    today = date.today()

    task_view = []
    for t in tasks:
        due_obj = parse_due(t.due_date)
        status = "none"

        if due_obj and not t.done:
            if due_obj < today:
                status = "overdue"
            elif due_obj == today:
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
    )


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    filter_type = request.args.get("filter", "all")
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("home", filter=filter_type))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    filter_type = request.args.get("filter", "all")
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("home", filter=filter_type))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    filter_type = request.args.get("filter", "all")
    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        task.title = request.form["title"].strip()
        task.due_date = request.form.get("due_date", "").strip() or None
        db.session.commit()
        return redirect(url_for("home", filter=filter_type))

    return render_template("edit.html", task=task, filter_type=filter_type)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
