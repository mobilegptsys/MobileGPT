import pinecone
import os

class Pinecone_Controller():
    def __init__(self, namespace_name):
        pinecone.init(
            api_key=os.getenv("PINECONE_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT")
        )

        self.index_name = "applist"
        self.pinecone_db = pinecone.Index(self.index_name)

        if namespace_name == os.getenv("MOBILEGPT_USER_NAME"):
            self.namespace_name = namespace_name
        else:
            self.namespace_name = namespace_name + "58485327"

    def upsert(self, vector):
        response = self.pinecone_db.upsert(vectors=vector, namespace=self.namespace_name)
        return response

    def get_candidates(self, vector, is_include_metadata=False):
        responses = self.pinecone_db.query(vector=vector, namespace=self.namespace_name, top_k=5, include_metadata=is_include_metadata)['matches']
        return responses
