import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec


# Load environment variables from a .env file if it exists
load_dotenv()


# Initialize the Pinecone client
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_env = os.getenv("PINECONE_ENV")


pc = Pinecone(api_key=pinecone_api_key)


# Create or connect to an existing Pinecone index
index_name = "medical-database"
if index_name not in [index.name for index in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region=pinecone_env
        )
    )


index = pc.Index(index_name)


def store_data_in_pinecone(embedding, metadata):
    try:
        index.upsert(
            vectors=[
                {
                    "id": metadata['id'],
                    "values": embedding,
                    "metadata": metadata
                }
            ]
        )
    except Exception as e:
        print(f"Error storing data in Pinecone: {e}")