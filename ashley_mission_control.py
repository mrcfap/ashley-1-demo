"""Painel operacional CLI local. Não inicia tarefas, não altera dados."""
import argparse
import json
from pathlib import Path
from app.operations.runtime import runtime_report, mission_report

def main():
    parser = argparse.ArgumentParser(description='Ashley Mission Control - diagnóstico local somente leitura')
    parser.add_argument('--root', default=str(Path(__file__).resolve().parent))
    parser.add_argument('--user-id', type=int, default=None, help='ID do usuário para consultar tarefas V22')
    parser.add_argument('--db', default=None, help='Caminho do banco V22; padrão ashley_coding_v22.db')
    args = parser.parse_args()
    result = {'runtime': runtime_report(args.root)}
    if args.user_id is not None:
        db = args.db or str(Path(args.root) / 'ashley_coding_v22.db')
        result['mission_control'] = mission_report(db, args.user_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
