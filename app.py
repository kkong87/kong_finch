from functools import wraps
from flask import Flask, request, redirect, render_template, session
from finch_api import FinchSetUp

app = Flask(__name__)
app.secret_key = "session_secret"

finch = FinchSetUp()


def require_finch_session(path):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            query_string = request.query_string.decode('utf-8')
            updated_path = "{}?{}".format(path, query_string) if query_string else path
            session["path"] = updated_path

            check_session = finch.check_session()
            if check_session:
                return redirect(check_session)

            result = func(*args, **kwargs)

            session["path"] = None
            return result

        return wrapper
    return decorator


@app.get("/")
def index():
    try:
        redirect_url = finch.check_session()
    
        return redirect(redirect_url if redirect_url else "/home")
    except Exception as e:
        return render_error(e)


@app.get("/set_code")
def set_code():
    code = request.args.get("code")
    finch.set_code(code)

    access_token = finch.get_auth()
    finch.set_access_token(access_token)

    print("code and token set")

    if session.get("path"):
        return redirect(session["path"])

    return redirect("/home")


@app.get("/home")
@require_finch_session("/home")
def get_homepage():
    try:
        company = finch.get_company()
    except Exception as e:
        return render_error(e)
    
    try:
        directory = finch.get_formatted_directory()
    except Exception as e:
        return render_error(e)

    return render_template(
        "homepage.html",
        company_data=company,
        directory_data=directory,
    )


@app.get("/company")
@require_finch_session("/company")
def get_company():
    try:
        return finch.get_company()
    except Exception as e:
        return render_error(e)


@app.get("/directory")
@require_finch_session("/directory")
def get_directory():
    try:
        return finch.get_directory()
    except Exception as e:
        return render_error(e)


@app.get("/employee")
@require_finch_session("/employee")
def get_employee():
    employee_id = request.args.get("id", False)
    if not employee_id:
        return "Missing Employee ID"
    try:
        individual = finch.get_individual(employee_id)
    except Exception as e:
        return render_error(e)
    
    try:
        employment = finch.get_employment(employee_id)
    except Exception as e:
        return render_error(e)

    return render_template(
        "employee.html",
        individual=individual,
        employment=employment,
    )


@app.get("/individual")
@require_finch_session("/individual")
def get_individual():
    employee_id = request.args.get("id", False)
    if not employee_id:
        return "Missing Employee ID"
    try:
        return finch.get_individual(employee_id)
    except Exception as e:
        return render_error(e)


@app.get("/employment")
@require_finch_session("/employment")
def get_employment():
    employee_id = request.args.get("id", False)
    if not employee_id:
        return "Missing Employee ID"
    return finch.get_employment(employee_id)

def render_error(error):
    if isinstance(error, Exception):
        message = str(error)
        error_body = None
    else:
        error_body = error.body

        message = error_body.get('message') if error_body.get('message') else error_body.get('error')

    return render_template(
        "error.html",
        error_message = message
    ), error_body.get('code') if error_body else 400


if __name__ == "__main__":
    app.run()

