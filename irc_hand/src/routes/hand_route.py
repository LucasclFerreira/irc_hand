# src/routes/hand_route.py
import os
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import pandas as pd

from src.services.hand_processor import process_hand_report

router = APIRouter()

@router.post("/upload-hand")
async def upload_hand_file(file: UploadFile = File(...)):
    """
    Endpoint para processamento de arquivo HAND
    
    Args:
        file (UploadFile): Arquivo CSV ou Excel para processamento
    
    Returns:
        Dict: Informações sobre os arquivos gerados
    """
    filename = file.filename.lower()
    if not filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Use CSV ou Excel.")
    
    unique_id = str(uuid.uuid4())
    temp_dir = "/tmp/hand_processing"
    os.makedirs(temp_dir, exist_ok=True)
    
    input_path = os.path.join(temp_dir, f"{unique_id}_{file.filename}")
    
    try:
        with open(input_path, "wb") as buffer:
            buffer.write(await file.read())
        
        try:
            df = pd.read_csv(input_path) if input_path.endswith('.csv') else pd.read_excel(input_path)
            required_columns = ['ADDRESS', 'TIV']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}"
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")
        
        report_paths = await process_hand_report(input_path)
        
        response = {
            "message": "Processamento concluído com sucesso",
            "files": report_paths
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")