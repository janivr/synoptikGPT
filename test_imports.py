import sys
import os

# Print current working directory
print("Current Working Directory:", os.getcwd())

# Print PYTHONPATH
print("\nPYTHONPATH:")
print(os.environ.get('PYTHONPATH', 'Not set'))

import os
print(os.listdir('src'))

import src.modules
print(src.modules.__file__)

# Add the project root and src directory to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

# Print Python path
print("\nPython Path:")
for path in sys.path:
    print(path)

# Now import
from src.utils.data_loader import DataLoader    
from src.utils.openai_helper import OpenAIHelper
from src.modules.buildings import BuildingsModule
from src.modules.financial import FinancialModule

def test_imports():
    print("\nSuccessfully imported modules:")
    print("BuildingsModule:", BuildingsModule)
    print("FinancialModule:", FinancialModule)
    print("DataLoader:", DataLoader)
    print("OpenAIHelper:", OpenAIHelper)

if __name__ == "__main__":
    test_imports()