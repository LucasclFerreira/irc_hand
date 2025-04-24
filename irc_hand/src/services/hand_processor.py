# src/services/hand_processor.py
import os
import asyncio
from typing import Dict, List

from hand_application import HandCalculator
from hand_report import HandReportGenerator

async def process_hand_report(input_path: str) -> Dict[str, str]:
    """
    Processa o arquivo de entrada gerando relatório HAND de forma assíncrona
    
    Args:
        input_path (str): Caminho do arquivo de entrada
    
    Returns:
        Dict[str, str]: Caminhos dos arquivos gerados
    """
    # Diretório temporário para processamento
    temp_dir = "/tmp/hand_processing"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Caminho para o template do relatório (considerando root)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    template_path = os.path.join(project_root, "Copia_de_Modelo_Relatorio_HAND.docx")
    
    # Gerar nome único para os arquivos de saída
    unique_id = os.path.splitext(os.path.basename(input_path))[0]
    
    # Processamento do modelo HAND
    loop = asyncio.get_event_loop()
    
    # Executar métodos síncronos em um executor para não bloquear
    calculator = await loop.run_in_executor(None, HandCalculator, "ee-irc")
    
    output_csv_path = os.path.join(temp_dir, f"{unique_id}_processed.csv")
    
    # Executar o processamento usando run_in_executor
    await loop.run_in_executor(
        None, 
        calculator.run, 
        input_path, 
        "ADDRESS", 
        output_csv_path, 
        True
    )
    
    # Geração do relatório
    report_generator = await loop.run_in_executor(
        None, 
        HandReportGenerator, 
        output_csv_path, 
        template_path, 
        temp_dir
    )
    
    # Gerar relatório
    doc_path, pdf_path = await loop.run_in_executor(None, report_generator.run, f"Relatorio_HAND_{unique_id}")
    
    # Preparar dicionário de retorno
    return_files = {"processed_csv": output_csv_path}
    
    if doc_path:
        return_files["docx"] = doc_path
    if pdf_path:
        return_files["pdf"] = pdf_path
    
    return return_files