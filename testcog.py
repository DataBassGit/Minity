#!/usr/bin/env python3
"""Simple chat script for testing PersonaMemory with installed AgentForge."""

from dotenv import load_dotenv
from agentforge.cog import Cog

# Load environment variables from .env file
load_dotenv()


def main():
    cog_test = Cog('TestCog')
    print("Cog is awaiting your input...")
    while True:
        user_input: str = input("You: ")
        if user_input.lower() == 'quit':
            print("Chao!")
            break

        result = cog_test.run(user_input=user_input)
        flow = cog_test.get_track_flow_trail()
        print(f"---------")
        print(flow)
        print(f"---------")
        print(f"Assistant: {result}")
        print(f"---------")


if __name__ == "__main__":
    main()
