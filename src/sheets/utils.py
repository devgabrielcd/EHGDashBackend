from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from .models import SheetData
from datetime import datetime

def get_sheets_service():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

def fetch_spreadsheet_data(spreadsheet_id, range_name):
    service = get_sheets_service()
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        print(f"Dados brutos da planilha {spreadsheet_id} (range {range_name}): {values}")
        return values
    except Exception as e:
        print(f"Erro ao buscar dados da planilha {spreadsheet_id} (range {range_name}): {e}")
        return []

def sync_spreadsheet_data():
    SPREADSHEET_ONE_ID = '1hCCNo_o8bk7IXva1KZt16FfTQX8m54FbQCxevjjNSt0'
    SPREADSHEET_TWO_ID = '1y6lTtqhdQOZSjoJViedVWD3hs9-F-jhgYfYAcp43UM0'
    # Ranges específicos para cada planilha, se necessário
    RANGE_ONE = 'Sheet1'  # Ajuste conforme a aba da primeira planilha
    RANGE_TWO = 'Sheet2!A1:Z100'  # Mantido como você definiu

    def process_data(spreadsheet_id, data):
        if not data or len(data) <= 1:
            print(f"Nenhum dado encontrado na planilha {spreadsheet_id}")
            return

        income_mapping = {
            '0-15k': '0k-15k',
            '15-30k': '15k-25k',
            '30-50k': '30k-50k',
            '50-75k': '50k-75k',
            '75-100k': '75k-100k',
        }

        for row in data[1:]:
            try:
                zipcode = int(row[0]) if len(row) > 0 and row[0].isdigit() else 0
                plan = row[1] if len(row) > 1 and row[1] in dict(SheetData.PLAN_CHOICES) else 'individual'
                type_ = row[2] if len(row) > 2 and row[2] in dict(SheetData.TYPE_CHOICES) else 'healthy'
                income_raw = row[3] if len(row) > 3 else '0k-15k'
                income = income_mapping.get(income_raw, '0k-15k')
                firstname = row[4] if len(row) > 4 else ''
                lastname = row[5] if len(row) > 5 else ''
                birth = datetime.strptime(row[6], '%Y-%m-%d').date() if len(row) > 6 else datetime.now().date()
                address = row[7] if len(row) > 7 else ''
                state = row[8] if len(row) > 8 else ''
                email = row[9] if len(row) > 9 else 'unknown@example.com'
                phone = row[10] if len(row) > 10 else ''

                defaults = {
                    'zipcode': zipcode,
                    'plan': plan,
                    'type': type_,
                    'income': income,
                    'firstname': firstname,
                    'lastname': lastname,
                    'birth': birth,
                    'address': address,
                    'city': '',
                    'state': state,
                    'email': email,
                    'phone': phone[:15],
                }
                obj, created = SheetData.objects.update_or_create(
                    spreadsheet_id=spreadsheet_id,
                    email=defaults['email'],
                    defaults=defaults
                )
                print(f"Registro {'criado' if created else 'atualizado'} na planilha {spreadsheet_id}: {obj}")
            except Exception as e:
                print(f"Erro ao processar linha {row} na planilha {spreadsheet_id}: {e}")

    data_one = fetch_spreadsheet_data(SPREADSHEET_ONE_ID, RANGE_ONE)
    process_data(SPREADSHEET_ONE_ID, data_one)

    data_two = fetch_spreadsheet_data(SPREADSHEET_TWO_ID, RANGE_TWO)
    process_data(SPREADSHEET_TWO_ID, data_two)