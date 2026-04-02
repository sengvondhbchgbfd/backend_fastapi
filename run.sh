
# set -e

# echo "🚀 Starting Backend Application..."

# # Load environment variables
# if [ -f .env ]; then
#     export $(cat .env | grep -v '#' | xargs)
# else
#     echo "⚠️  .env file not found. Using defaults or environment variables."
# fi

# # Check if Python is installed
# if ! command -v python3 &> /dev/null; then
#     echo "❌ Python3 is not installed"
#     exit 1
# fi

# # Install/upgrade pip
# echo "📦 Installing dependencies..."
# python3 -m pip install --upgrade pip

# # Install requirements
# if [ -f requirements.txt ]; then
#     pip install -r requirements.txt
# else
#     echo "⚠️  requirements.txt not found"
# fi

# echo "✅ Starting application on http://localhost:8000"
# python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# =====================================================================
