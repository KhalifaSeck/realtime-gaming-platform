"""Wrapper httpx pour l'API FastAPI, avec cache Streamlit."""
from __future__ import annotations

import httpx
import streamlit as st

from config import get_settings


def _client() -> httpx.Client:
    return httpx.Client(base_url=get_settings().api_base_url, timeout=30.0)


@st.cache_data(ttl=30, show_spinner=False)
def get(path: str, **params) -> dict:
    """GET sur l'API. Cache 30s. params passes en query string."""
    with _client() as c:
        r = c.get(path, params=params)
        r.raise_for_status()
        return r.json()