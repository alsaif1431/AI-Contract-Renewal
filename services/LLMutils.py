import streamlit as st
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key= st.secrets.get('AZURE_OPENAI_API_KEY'),
    api_version=st.secrets.get('AZURE_API_VERSION'),
    azure_endpoint=st.secrets.get('AZURE_API_ENDPOINT'),
)