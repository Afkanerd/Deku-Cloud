"""User API Endpoints"""

import logging
import json
from datetime import timedelta

from flask import request, Blueprint, Response, jsonify

from werkzeug.exceptions import InternalServerError, BadRequest, Conflict, Unauthorized

from settings import Configurations
from src.schemas.db_connector import connection

from src.models.users import UserModel
from src.models.projects import ProjectModel
from src.models.sessions import SessionModel

logger = logging.getLogger(__name__)

v1 = Blueprint("v1", __name__)

COOKIE_NAME = Configurations.COOKIE_NAME
COOKIE_LIFETIME = Configurations.COOKIE_LIFETIME


@v1.after_request
def after_request(response):
    """After request decorator"""
    try:
        connection.close()
        return response

    except Exception as error:
        logger.exception(error)
        return "Internal Server Error", 500


@v1.route("/signup", methods=["POST"])
def signup():
    """Signup Endpoint"""

    try:
        if not request.headers.get("User-Agent"):
            logger.error("[!] No user agent")
            raise BadRequest()

        if not request.json.get("email"):
            logger.error("[!] No email provided")
            raise BadRequest()

        if not request.json.get("password"):
            logger.error("[!] No password provided")
            raise BadRequest()

        email = request.json.get("email")
        password = request.json.get("password")
        name = request.json.get("name")
        phone_number = request.json.get("phone_number")

        user = UserModel()

        user.create(
            email=email,
            password=password,
            name=name,
            phone_number=phone_number,
        )

        return "", 200

    except BadRequest as err:
        return str(err), 400

    except Unauthorized as err:
        return str(err), 401

    except Conflict as err:
        return str(err), 409

    except InternalServerError as err:
        logger.exception(err)
        return "Internal Server Error", 500

    except Exception as error:
        logger.exception(error)
        return "Internal Server Error", 500


@v1.route("/login", methods=["POST"])
def login():
    """Login Endpoint"""

    try:
        if not request.headers.get("User-Agent"):
            logger.error("[!] No user agent")
            raise BadRequest()

        if not request.json.get("email"):
            logger.error("[!] No email provided")
            raise BadRequest()

        if not request.json.get("password"):
            logger.error("[!] No password provided")
            raise BadRequest()

        user_agent = request.headers.get("User-Agent")
        email = request.json.get("email")
        password = request.json.get("password")
        status = "active"

        user = UserModel()
        session = SessionModel(session_lifetime=COOKIE_LIFETIME)

        user_ = user.verify(email=email, password=password)

        session_ = session.create(
            unique_identifier=user_.id, user_agent=user_agent, status=status
        )

        res = Response()

        session_data = json.loads(session_.data)

        res.set_cookie(
            COOKIE_NAME,
            str(session_.sid),
            max_age=timedelta(milliseconds=session_data["maxAge"]),
            secure=session_data["secure"],
            httponly=session_data["httpOnly"],
            samesite=session_data["sameSite"],
        )

        return res, 200

    except BadRequest as err:
        return str(err), 400

    except Conflict as err:
        return str(err), 409

    except Unauthorized as err:
        return str(err), 401

    except InternalServerError as err:
        logger.exception(err)
        return "Internal Server Error", 500

    except Exception as error:
        logger.exception(error)
        return "Internal Server Error", 500


@v1.route("/projects", methods=["POST"])
def create_project():
    """Create Project Endpoint"""

    try:
        if not request.headers.get("User-Agent"):
            logger.error("[!] No user agent")
            raise BadRequest()

        if not request.json.get("name"):
            logger.error("[!] No name provided")
            raise BadRequest()

        if not request.cookies.get(COOKIE_NAME):
            logger.error("[!] No cookie")
            raise Unauthorized()

        user_agent = request.headers.get("User-Agent")
        sid = request.cookies.get(COOKIE_NAME)
        name = request.json.get("name")
        status = "active"

        project = ProjectModel()
        session = SessionModel(session_lifetime=COOKIE_LIFETIME)

        session_ = session.find(sid=sid, user_agent=user_agent, status=status)

        project_ = project.create(
            name=name,
            user_id=session_.unique_identifier,
        )

        session_ = session.update(sid=sid, user_agent=user_agent)

        res = jsonify(
            {
                "id": project_.project_ref,
                "name": project_.name,
                "created_at": project_.created_at,
            }
        )

        session_data = json.loads(session_.data)

        res.set_cookie(
            COOKIE_NAME,
            str(session_.sid),
            max_age=timedelta(milliseconds=session_data["maxAge"]),
            secure=session_data["secure"],
            httponly=session_data["httpOnly"],
            samesite=session_data["sameSite"],
        )

        return res, 200

    except BadRequest as err:
        return str(err), 400

    except Unauthorized as err:
        return str(err), 401

    except Conflict as err:
        return str(err), 409

    except InternalServerError as err:
        logger.exception(err)
        return "Internal Server Error", 500

    except Exception as error:
        logger.exception(error)
        return "Internal Server Error", 500
