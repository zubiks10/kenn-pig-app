import os
import subprocess
import sys

# -------------------------------
# Helper functions
# -------------------------------
def run(cmd, check=True):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def create_venv(venv_dir="venv"):
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        run(f"{sys.executable} -m venv {venv_dir}")
    else:
        print("Virtual environment already exists.")

def get_pip_executable(venv_dir="venv"):
    if os.name == "nt":  # Windows
        return os.path.join(venv_dir, "Scripts", "pip.exe")
    else:  # macOS/Linux
        return os.path.join(venv_dir, "bin", "pip")

def get_python_executable(venv_dir="venv"):
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        return os.path.join(venv_dir, "bin", "python")

# -------------------------------
# Step 1: Create venv
# -------------------------------
venv_dir = "venv"
create_venv(venv_dir)

pip_exe = get_pip_executable(venv_dir)
python_exe = get_python_executable(venv_dir)

# -------------------------------
# Step 2: Upgrade pip
# -------------------------------
run(f"{pip_exe} install --upgrade pip")

# -------------------------------
# Step 3: Reorder requirements.txt (ultralytics first)
# -------------------------------
if not os.path.exists("requirements.txt"):
    print("Error: requirements.txt not found!")
    sys.exit(1)

with open("requirements.txt", "r") as f:
    lines = [line.strip() for line in f if line.strip()]

ultra = [line for line in lines if line.lower() == "ultralytics"]
others = [line for line in lines if line.lower() != "ultralytics"]

# Rewriting requirements.txt with ultralytics at the top
with open("requirements.txt", "w") as f:
    for line in ultra + others:
        f.write(line + "\n")

# -------------------------------
# Step 4: Install all packages
# -------------------------------
run(f"{pip_exe} install -r requirements.txt")

# -------------------------------
# Step 5: Run Streamlit app
# -------------------------------
print("Starting Streamlit dashboard...")
run(f"{python_exe} -m streamlit run r3_dashboardStreamlit.py --server.address 0.0.0.0 --server.port 8501")
