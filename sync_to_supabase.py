import os
import pandas as pd
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SHAREPOINT_URL = os.environ.get("SHAREPOINT_URL")

def sync_data():
    print("A descarregar a planilha diretamente do SharePoint...")
    
    # Ajusta o link do SharePoint para forçar o descarregamento direto
    download_url = SHAREPOINT_URL.replace("web=1", "download=1")
    
    response = requests.get(download_url)
    if response.status_code != 200:
        raise Exception(f"Erro ao descarregar o ficheiro do SharePoint. Código: {response.status_code}")
        
    with open("temp_data.xlsx", "wb") as f:
        f.write(response.content)

    print("A ler a aba ENFERMAGEM...")
    df = pd.read_excel("temp_data.xlsx", sheet_name="ENFERMAGEM")
    df = df.where(pd.notnull(df), None)
    
    print(f"Total de registos encontrados: {len(df)}")
    
    records = []
    for _, row in df.iterrows():
        record = {
            "colaborador": str(row.iloc[0]) if row.iloc[0] is not None else "",
            "setor": str(row.iloc[1]) if row.iloc[1] is not None else "",
            "grupo": str(row.iloc[2]) if row.iloc[2] is not None else "",
            "cargo": str(row.iloc[3]) if row.iloc[3] is not None else "",
            "gestor_nome": str(row.iloc[4]) if row.iloc[4] is not None else "",
            "uf": str(row.iloc[5]) if row.iloc[5] is not None else "",
            "curso": str(row.iloc[6]) if row.iloc[6] is not None else "",
            "status": str(row.iloc[7]) if row.iloc[7] is not None else "",
            "nota_pre": float(row.iloc[8]) if pd.notnull(row.iloc[8]) else None,
            "nota_pos": float(row.iloc[9]) if pd.notnull(row.iloc[9]) else None,
        }
        records.append(record)

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    url = f"{SUPABASE_URL}/rest/v1/qualitotal_dados"

    print("A limpar dados antigos na tabela do Supabase...")
    requests.delete(f"{url}?id=gt.0", headers=headers)

    print("A enviar novos dados para o Supabase em lotes...")
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        res = requests.post(url, headers=headers, json=batch)
        if res.status_code >= 400:
            print(f"Erro ao inserir lote {i}: {res.text}")
        else:
            print(f"Lote {i} a {i+len(batch)} enviado com sucesso!")

    print("Sincronização concluída com sucesso!")

if __name__ == "__main__":
    sync_data()
