from agentforge.storage.chroma_storage import ChromaStorage
from CustomAgents.Trinity.JournalAgent import JournalAgent
from CustomAgents.Trinity.JournalThoughtAgent import JournalThoughtAgent
from Utilities.Parsers import MessageParser
import os
from datetime import datetime
import agentforge.tools.semantic_chunk as Chunker


class Journal:
    """
    Manages the creation, storage, and retrieval of journal entries.
    """

    def __init__(self):
        """
        Initialize the Journal with necessary components for storage, parsing, and agent interactions.
        """
        print("Journal initializing")
        self.storage = ChromaStorage()
        self.parser = MessageParser
        self.journal = JournalAgent()
        self.journalthought = JournalThoughtAgent()
        self.results = ''
        self.filepath = ''
        self.thoughts = None

    def do_journal(self):
        """
        Execute the full journaling process: write entry, reflect, save, and store in database.

        Returns:
            str: The generated journal entry.
        """
        print("Do Journal")
        self.write_entry()
        print("Write Entry")
        self.journal_reflect()
        print("Journal Reflect")
        try:
            path = self.save_journal()
            print(f"File created: {path}")
        except Exception as e:
            print(f"Exception occurred {e}")
        self.journal_to_db()
        return self.results

    def write_entry(self):
        """
        Generate a new journal entry using the JournalAgent.

        Returns:
            str: The generated journal entry.
        """
        collection = 'journal_log_table'
        print("Write Entry Collection")
        log = self.storage.load_collection(collection_name=collection)
        print("Write Entry Log")
        messages = self.parser.format_journal_entries(log)
        self.results = self.journal.run(chat_log=messages)
        return self.results

    def journal_reflect(self):
        """
        Reflect on the generated journal entry using the JournalThoughtAgent.

        Returns:
            dict: Parsed thoughts about the journal entry.
        """
        thoughts = self.journalthought.run(journal_entry=self.results)
        parsed_thoughts = self.parser.parse_lines(thoughts)
        self.thoughts = parsed_thoughts
        return self.thoughts

    def save_journal(self):
        """
        Save the journal entry to a unique markdown file.

        Returns:
            str: The path of the created file.
        """
        folder_path = os.path.join(os.getcwd(), 'Journal')
        file_name = datetime.now().strftime('%Y-%m-%d')
        # Ensure the folder exists, create it if not
        os.makedirs(folder_path, exist_ok=True)

        # Find existing files with the same name prefix
        existing_files = [f for f in os.listdir(folder_path) if f.startswith(file_name) and f.endswith(".md")]

        # Generate a unique file name based on the count of existing files
        unique_file_name = file_name
        if existing_files:
            count = len(existing_files)
            unique_file_name = f"{file_name}_{count}"

        # Create the file path
        self.file_path = os.path.join(folder_path, unique_file_name + ".md")

        # Write the content to the file
        with open(self.file_path, "w", encoding="utf-8") as file:
            file.write(self.results)

        return self.file_path

    def journal_to_db(self):
        """
        Store the journal entry and its chunks in the database.
        """
        # whole entry
        sourceid = self.storage.count_collection('whole_journal_entries')
        source_id_string = [str(sourceid + 1)]
        metadata = {
            "id": sourceid + 1,
            "Source": self.filepath,
            "Categories": self.thoughts['Categories'],
            "Inner Thought": self.thoughts['Inner Thought'],
            "Reason": self.thoughts['Reason']
        }
        self.storage.save_memory(collection_name='whole_journal_entries', data=self.results, ids=source_id_string, metadata=[metadata])
        print(f"Saved journal entry:\n\n{self.results}\nMetadata:\n{metadata}\n-----")

        # chunked for lookup
        chunks = Chunker.semantic_chunk(self.results)

        for chunk in chunks:
            collection_size = self.storage.count_collection('journal_chunks_table')
            memory_id = [str(collection_size + 1)]
            metadata = {
                "id": collection_size + 1,
                "Source": self.filepath,
                "Source_ID": sourceid + 1,
            }
            print(f"Saved chunk:\n\n{chunk.content}\nMetadata:\n{metadata}\n=====")

            self.storage.save_memory(collection_name='journal_chunks_table', data=chunk.content, ids=memory_id, metadata=[metadata])

    def load_journals_from_backup(self, folder_path):
        """
        Load journal entries from markdown files in a specified folder.

        Args:
            folder_path (str): Path to the folder containing journal markdown files.
        """
        for filename in os.listdir(folder_path):
            # Check if the file has a .md extension
            if filename.endswith(".md"):
                file_path = os.path.join(folder_path, filename)
                self.filepath = os.path.abspath(file_path)

                # Read the contents of the file
                with open(self.filepath, "r", encoding="utf-8") as file:
                    file_contents = file.read()

                # Print the file contents
                print(f"Contents of {filename}:")
                print(file_contents)
                print("---")
                self.results = file_contents
                self.journal_reflect()
                self.journal_to_db()


if __name__ == '__main__':
    # Loads Journals from saved journal entries.
    # This will send each journal to the LLM and generate
    # thoughts, in a similar manner to the thought agent.
    # All journals must be .md files.
    journal = Journal()
    folder_path = "..\\Journal"
    journal.load_journals_from_backup(folder_path)