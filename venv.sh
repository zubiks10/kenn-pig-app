# Create virtual environment if it doesn't exist
if [ ! -d "myenv" ]; then
  python3 -m venv myenv
fi

# Activate the virtual environment
. myenv/bin/activate

# Show installed packages
pip list
