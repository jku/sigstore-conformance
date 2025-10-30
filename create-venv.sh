# uv allows us to easily manage python versions for our venvs... but uv is not always available.
# Assume that there is *some* Python available and use a bootstrap venv using the system python to
#   1. install uv & the python we want
#   2. create the actual venv with the installed python
#   3. install uv in the actual venv
# Now the actual venv is ready to use

if [ -z "$1" ]; then
    echo "Error: No virtual environment path provided." >&2
    echo "Usage: $0 <venv_path>" >&2
    exit 1
fi

ENV=$1
PYTHON_VERSION="3.14"

BOOTSTRAP_ENV=$(mktemp -d)
python3 -m venv --clear $BOOTSTRAP_ENV
. $BOOTSTRAP_ENV/bin/activate && pip install uv && uv venv $ENV --python $PYTHON_VERSION && VIRTUAL_ENV=$ENV uv pip install uv
touch $ENV/bootstrap
