

#RÉCUPÉRATION D'UN ANCIEN CODE POUR VOIR SI ÇA MARCHE
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Tuple, Set
import numpy as np
import tiktoken
import umap.umap_ as umap
from sklearn.mixture import GaussianMixture
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_random_exponential
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
import re
import webbrowser
import os
import datamapplot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS and OpenAI API credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = 'ap-southeast-2'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Seed for reproducibility
RANDOM_SEED = 224
random.seed(RANDOM_SEED)

SYSTEM_PROMPT = """You are a helpful tool to summarize user interactions in any domain."""
PROMPT = "The provided interactions are written by students to an assistant. Provide a concise summary of WHAT the student is requesting. Do not make mention of the students. Limit the summary to 10 words or fewer: {context}\nSummary: "

# Abstract class for clustering algorithm
class ClusteringAlgorithm(ABC):
    @abstractmethod
    def perform_clustering(self, embeddings: np.ndarray, **kwargs) -> List[List[int]]:
        pass

# Node class representing each point in the tree
class Node:
    def __init__(self, text: str, index: int, children: Set[int], embeddings) -> None:
        self.text = text
        self.index = index
        self.children = children
        self.embeddings = embeddings

# Tree structure
class Tree:
    def __init__(self, all_nodes, root_nodes, leaf_nodes, num_layers, layer_to_nodes) -> None:
        self.all_nodes = all_nodes
        self.root_nodes = root_nodes
        self.leaf_nodes = leaf_nodes
        self.num_layers = num_layers
        self.layer_to_nodes = layer_to_nodes

# RAPTOR clustering algorithm
class RAPTOR_Clustering(ClusteringAlgorithm):
    def perform_clustering(
        nodes: List[Node],
        embedding_model_name: str,
        max_length_in_cluster: int = 3500,
        tokenizer=tiktoken.get_encoding("cl100k_base"),
        reduction_dimension: int = 10,
        threshold: float = 0.1,
        verbose: bool = False,
    ) -> List[List[Node]]:
        embeddings = np.array([node.embeddings[embedding_model_name] for node in nodes])
        clusters = perform_clustering(embeddings, dim=reduction_dimension, threshold=threshold)
        print(clusters)
        node_clusters = []
        for label in np.unique(np.concatenate(clusters)):
            indices = [i for i, cluster in enumerate(clusters) if label in cluster]
            cluster_nodes = [nodes[i] for i in indices]
            if len(cluster_nodes) == 1:
                node_clusters.append(cluster_nodes)
                continue
            total_length = sum([len(tokenizer.encode(node.text)) for node in cluster_nodes])
            if total_length > max_length_in_cluster:
                print(f"Reclustering cluster with {len(cluster_nodes)} nodes")
                node_clusters.extend(
                    RAPTOR_Clustering.perform_clustering(
                        cluster_nodes, embedding_model_name, max_length_in_cluster
                    )
                )
            else:
                node_clusters.append(cluster_nodes)
        return node_clusters

# Singleton DynamoDB client
class DynamoDBClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            print("Creating new instance of DynamoDBClient")
            try:
                cls._instance = super(DynamoDBClient, cls).__new__(cls)
                cls.client = boto3.resource(
                    'dynamodb',
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                )
                print("DynamoDBClient initialized successfully")
            except Exception as e:
                print(f"Failed to initialize DynamoDBClient: {e}")
        else:
            print("Using existing instance of DynamoDBClient")
        return cls._instance

# Singleton OpenAI API client
class OpenAIApiClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(OpenAIApiClient, cls).__new__(cls)
            cls.text_embeddings = OpenAIEmbeddings(
                openai_api_key=OPENAI_API_KEY,
                model="text-embedding-ada-002"
            )
            cls.open_ai_client = OpenAI(api_key=OPENAI_API_KEY)
        return cls._instance

# Extract plot data from HTML
def extract_plot_data(html_string):
    pattern = re.compile(r'const\s+(point|hover|label)DataBase64\s*=\s*"([^"]+)"')
    matches = pattern.findall(html_string)
    extracted_data = {"pointDataBase64": None, "hoverDataBase64": None, "labelDataBase64": None}
    for match in matches:
        data_type, data_value = match
        extracted_data[data_type + "DataBase64"] = data_value
    return extracted_data

# Retry wrapper for getting text embeddings
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_text_embedding(text, model="text-embedding-ada-002"):
    client = OpenAIApiClient().open_ai_client
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

# Base class for summarization models
class BaseSummarizationModel(ABC):
    @abstractmethod
    def summarize(self, context, max_tokens=150):
        pass

# GPT-3.5 Turbo summarization model
class GPT3TurboSummarizationModel(BaseSummarizationModel):
    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def summarize(self, context, max_tokens=500, stop_sequence=None):
        try:
            client = OpenAIApiClient().open_ai_client
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": PROMPT.format(context=context)},
                ],
                max_tokens=max_tokens,
            )
            return get_string_after_colon(response.choices[0].message.content)
        except Exception as e:
            print(e)
            return e

# Helper function for padding or truncating sequences
def pad_or_truncate(sequence, desired_length, padding_value=""):
    if len(sequence) > desired_length:
        return sequence[:desired_length]
    else:
        return sequence + [padding_value] * (desired_length - len(sequence))

# Get node labels with homogenization of sequences
def get_node_labels(tree, embedding_model="OpenAI", desired_length=5):
    idx_to_node = {node.index: [node.text] for node in tree[len(tree) - 1]}
    num_layers = len(tree)
    layer = num_layers - 1
    while layer > 0:
        layer_labels = {node.index: [node.text] for node in tree[layer - 1]}
        for node in tree[layer]:
            for children in node.children:
                layer_labels[children].extend(idx_to_node[node.index])
        idx_to_node = layer_labels
        layer -= 1
    
    # Get embeddings and homogenize sequences
    embeddings = [node.embeddings[embedding_model] for node in tree[0]]
    idx_values = list(idx_to_node.values())
    idx_values_homogeneous = [pad_or_truncate(seq, desired_length) for seq in idx_values]

    return embeddings, np.array(idx_values_homogeneous)

# Function to create the cluster plot
def create_cluster_plot(course_id: str):
    logging.info(f"Getting Course {course_id} messages")
    messages = get_course_chat_messages(course_id=course_id, start_date=datetime.now() - timedelta(days=40), end_date=datetime.now())
    messages = [message['body'] for message in messages]
    logging.info(f"Received {len(messages)} messages for course: {course_id}")
    if len(messages) == 0:
        return {"error": "No messages for course id " + course_id}
    
    logging.info(f"Getting Embeddings for course: {course_id}")
    leaf_nodes = {}
    for index, text in enumerate(messages):
        _, node = create_node(index, text)
        leaf_nodes[index] = node

    logging.info(f"Constructing RAPTOR tree for course: {course_id}")
    tree = construct_tree(leaf_nodes)

    logging.info(f"Getting node labels for course: {course_id}")
    embeddings, labels = get_node_labels(tree)

    logging.info(f"Getting Reduced Embeddings for course: {course_id}")
    reduced_embeddings = global_cluster_embeddings(embeddings=embeddings, dim=2)

    logging.info(f"Creating interactive plot for course: {course_id}")
    plot_html = str(datamapplot.create_interactive_plot(
        reduced_embeddings,
        labels[:, 0],  # Access first column of labels
        labels[:, 1],  # Access second column of labels
        hover_text=labels[:, 0],
        font_family="UI Sans Serif",
        enable_search=True,
    ))

    output_file = "/Users/gregoryhissiger/lucy_backend_web_action_proto1/cluster_html_fake_demo_yc/cluster_plot_test_with_yc_data.html"
    with open(output_file, "w") as file:
        file.write(plot_html)
    logging.info(f"Graph for course {course_id} saved to {output_file}")

    return {'plot_html': plot_html, 'plot_data': extract_plot_data(plot_html)}

# Function to query DynamoDB for course chat messages
def get_course_chat_messages(course_id: str, start_date: datetime, end_date: datetime = datetime.now()):
    try:
        response = table.query(
            IndexName='course_id-index',
            KeyConditionExpression='course_id = :course_id AND #ts BETWEEN :start_date AND :end_date',
            FilterExpression='username <> :lucy_username',
            ExpressionAttributeValues={
                ':course_id': course_id,
                ':start_date': start_date.isoformat(),
                ':end_date': end_date.isoformat(),
                ':lucy_username': "Lucy"
            },
            ExpressionAttributeNames={
                "#ts": "timestamp"
            },
            ScanIndexForward=True
        )
        return response.get('Items', [])
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error querying chats for course with ID {course_id}: {error_code} - {error_message}")
        return []

# Create node function
def create_node(index: int, text: str, children_indices: Optional[Set[int]] = None) -> Tuple[int, Node]:
    if children_indices is None:
        children_indices = set()
    embeddings = {"OpenAI": get_text_embedding(text)}
    return (index, Node(text, index, children_indices, embeddings))

# Utility function to extract text from node list
def get_text(node_list: List[Node]) -> str:
    text = ""
    for node in node_list:
        text += f"{' '.join(node.text.splitlines())}"
        text += "\n"
    return text

# Function to get node list
def get_node_list(node_dict: Dict[int, Node]) -> List[Node]:
    indices = sorted(node_dict.keys())
    node_list = [node_dict[index] for index in indices]
    return node_list

# Utility function to extract string after colon
def get_string_after_colon(input_string):
    colon_index = input_string.find(':')
    if colon_index != -1:
        result_string = input_string[colon_index + 1:].strip()
        return result_string
    return input_string

# Table setup for DynamoDB
table = DynamoDBClient().client.Table("MVP_chat_academic_advisor")

# Main execution
if __name__ == "__main__":
    result = create_cluster_plot("6f9b98d4-7f92-4f7b-abe5-71c2c634edb2")  # ID for the academic advisor course
    if 'error' in result:
        print(result['error'])
    else:
        output_file = "cluster_plot_test_with_yc_data.html"
        with open(output_file, "w") as file:
            file.write(result['plot_html'])
        webbrowser.open('file://' + os.path.realpath(output_file))
