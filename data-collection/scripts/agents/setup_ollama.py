#!/usr/bin/env python3
"""
OLLAMA SETUP SCRIPT

Checks if Ollama is installed and running, pulls required models if missing.

Models used by the pipeline:
- llama3.2     : Primary model for Auditor/Finalizer agents (good general reasoning)
- mistral      : Fallback model (faster, lighter)
- deepseek-r1  : Analysis model for Discoverer agent (strong numerical reasoning)

Usage:
    python setup_ollama.py
    python setup_ollama.py --models llama3.2 mistral
    python setup_ollama.py --check-only
"""

import subprocess
import sys
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_MODELS = ["llama3.2", "mistral", "deepseek-r1"]
OLLAMA_BASE_URL = "http://localhost:11434"


def check_ollama_installed() -> bool:
    """Check if Ollama CLI is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            logger.info(f"Ollama installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"Error checking Ollama: {e}")
    return False


def check_ollama_running() -> bool:
    """Check if Ollama server is running."""
    try:
        import requests
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def start_ollama_server():
    """Attempt to start the Ollama server."""
    logger.info("Starting Ollama server...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait for server to start
        for i in range(10):
            time.sleep(2)
            if check_ollama_running():
                logger.info("Ollama server started successfully")
                return True
            logger.info(f"  Waiting for server... ({i+1}/10)")
    except Exception as e:
        logger.error(f"Failed to start Ollama server: {e}")
    return False


def get_installed_models() -> list:
    """Get list of installed Ollama models."""
    try:
        import requests
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [m['name'].split(':')[0] for m in data.get('models', [])]
    except Exception as e:
        logger.warning(f"Error listing models: {e}")
    return []


def pull_model(model_name: str) -> bool:
    """Pull an Ollama model."""
    logger.info(f"Pulling model '{model_name}'... (this may take a while)")
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=False, text=True, timeout=1800  # 30 min timeout
        )
        if result.returncode == 0:
            logger.info(f"Successfully pulled '{model_name}'")
            return True
        else:
            logger.error(f"Failed to pull '{model_name}'")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout pulling '{model_name}'")
        return False
    except Exception as e:
        logger.error(f"Error pulling '{model_name}': {e}")
        return False


def setup(models: list = None, check_only: bool = False):
    """
    Full setup flow:
    1. Check Ollama installed
    2. Check/start server
    3. Pull missing models
    """
    models = models or DEFAULT_MODELS
    
    print("=" * 60)
    print("  OLLAMA SETUP FOR FINANCIAL DATA PIPELINE")
    print("=" * 60)

    # Step 1: Check installation
    if not check_ollama_installed():
        print("\n❌ Ollama is NOT installed.")
        print("   Install from: https://ollama.com/download")
        print("   Or run: curl -fsSL https://ollama.ai/install.sh | sh")
        return False

    # Step 2: Check/start server
    if not check_ollama_running():
        print("\n⚠️  Ollama server is not running.")
        if check_only:
            print("   Start with: ollama serve")
            return False
        if not start_ollama_server():
            print("   ❌ Could not start Ollama server.")
            print("   Start manually with: ollama serve")
            return False

    print("\n✅ Ollama server is running")

    # Step 3: Check/pull models
    installed = get_installed_models()
    print(f"\n📦 Installed models: {installed if installed else 'none'}")

    if check_only:
        missing = [m for m in models if m not in installed]
        if missing:
            print(f"\n⚠️  Missing models: {missing}")
            print(f"   Pull with: python setup_ollama.py --models {' '.join(missing)}")
            return False
        print("\n✅ All required models are available")
        return True

    all_ok = True
    for model in models:
        if model in installed:
            print(f"  ✅ {model} - already installed")
        else:
            print(f"  ⬇️  {model} - pulling...")
            if not pull_model(model):
                print(f"  ❌ {model} - FAILED to pull")
                all_ok = False
            else:
                print(f"  ✅ {model} - installed")

    if all_ok:
        print("\n✅ Setup complete! All models ready.")
    else:
        print("\n⚠️  Some models failed to install. The pipeline will use available models.")
    
    return all_ok


def main():
    parser = argparse.ArgumentParser(description='Setup Ollama for financial data pipeline')
    parser.add_argument(
        '--models', nargs='+', default=DEFAULT_MODELS,
        help=f'Models to install (default: {" ".join(DEFAULT_MODELS)})'
    )
    parser.add_argument(
        '--check-only', action='store_true',
        help='Only check status, do not install anything'
    )
    args = parser.parse_args()
    
    success = setup(models=args.models, check_only=args.check_only)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
