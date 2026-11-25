from dotenv import load_dotenv

load_dotenv()

from agents.company_agent import run

print(run("Write your risk assessment for Article 34."))