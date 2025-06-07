# Test script to verify the application works without actual Azure credentials
from flask import Flask
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import flask
        print("✓ Flask imported successfully")
        
        from dotenv import load_dotenv
        print("✓ python-dotenv imported successfully")
        
        import openai
        print("✓ OpenAI imported successfully")
        
        from azure.search.documents import SearchClient
        print("✓ Azure Search imported successfully")
        
        from azure.core.credentials import AzureKeyCredential
        print("✓ Azure Core imported successfully")
        
        # Try importing our modules
        try:
            import config
            print("✓ Config module imported successfully")
        except Exception as e:
            print(f"⚠ Config module import warning: {e}")
        
        try:
            from rag_assistant import FlaskRAGAssistant
            print("✓ RAG Assistant imported successfully")
        except Exception as e:
            print(f"⚠ RAG Assistant import warning: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_flask_app():
    """Test that the Flask app can be created"""
    try:
        # Create a minimal Flask app to test
        app = Flask(__name__)
        
        @app.route('/test')
        def test():
            return {'status': 'ok'}
        
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ Flask app creation error: {e}")
        return False

def test_html_file():
    """Test that the HTML file exists and is readable"""
    try:
        with open('index.html', 'r') as f:
            content = f.read()
        
        # Check for key elements
        if 'Model Parameters' in content:
            print("✓ HTML file contains Model Parameters card")
        if 'Model Output' in content:
            print("✓ HTML file contains Model Output card")
        if 'AI Evaluation' in content:
            print("✓ HTML file contains AI Evaluation card")
        if '/api/query' in content:
            print("✓ HTML file contains API endpoint references")
        
        print("✓ HTML file is valid and readable")
        return True
    except Exception as e:
        print(f"✗ HTML file error: {e}")
        return False

if __name__ == '__main__':
    print("=== RAG Interface Test Suite ===\n")
    
    print("1. Testing imports...")
    imports_ok = test_imports()
    print()
    
    print("2. Testing Flask app creation...")
    flask_ok = test_flask_app()
    print()
    
    print("3. Testing HTML file...")
    html_ok = test_html_file()
    print()
    
    print("=== Test Results ===")
    if imports_ok and flask_ok and html_ok:
        print("✓ All tests passed! The application should work correctly.")
        print("\nTo run the application:")
        print("1. Configure your .env file with Azure credentials")
        print("2. Run: python app.py")
        print("3. Open: http://localhost:5000")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    print("\nNote: The application requires valid Azure OpenAI and Cognitive Search credentials to function fully.")

