# First time

uv init --lib TodoApp

uv venv

uv add -r .\requirements.txt

# when pulling from git

uv venv

uv sync

uv add passlib
uv add bcrypt==4.0.1
uv add python-multipart
uv add "python-jose[cryptography]"
