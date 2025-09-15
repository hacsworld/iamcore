from dotenv import load_dotenv
load_dotenv()from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn, os, pathlib, time, hashlib, datetime, threading, json
import numpy as npfrom sentence_transformers import SentenceTransformer
from generation import generate_answer, use_generation
from humor import HumorEngineapp = FastAPI(title="Resonance Core (HACS)", version="3.4-prod")  # Grok: updated version

