from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import json
import io
import pandas as pd

class ExcelService:
    """Service for Excel operations and Account data handling"""
    
    def __init__(self):
        # RingCentral Brand Colors
        self.rc_cerulean = "0684BC"      # RingCentral primary blue
        self.rc_orange = "FF7A00"        # RingCentral orange
        self.rc_ocean = "002855"         # RingCentral dark blue
        self.rc_linen = "F1EFEC"         # RingCentral background
        self.rc_ash = "C8C2B4"           # RingCentral light gray
        self.rc_warm_black = "2B2926"    # RingCentral dark gray
        
        # Excel Styling with RingCentral Colors
        self.header_font = Font(bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color=self.rc_cerulean, end_color=self.rc_cerulean, fill_type="solid")
        self.summary_font = Font(bold=True, color=self.rc_ocean)
        self.summary_fill = PatternFill(start_color=self.rc_linen, end_color=self.rc_linen, fill_type="solid")
        self.title_font = Font(bold=True, size=16, color=self.rc_ocean)
        self.accent_fill = PatternFill(start_color=self.rc_orange, end_color=self.rc_orange, fill_type="solid")
        self.border = Border(
            left=Side(style='thin', color=self.rc_ash),
            right=Side(style='thin', color=self.rc_ash),
            top=Side(style='thin', color=self.rc_ash),
            bottom=Side(style='thin', color=self.rc_ash)
        )
        self.center_alignment = Alignment(horizontal='center', vertical='center')
        self.wrap_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    

    
    
    

    
    def parse_excel_file(self, file_content):
        """Parse uploaded Excel file and return sheet names and preview data"""
        try:
            # Load workbook from file content
            wb = load_workbook(io.BytesIO(file_content), read_only=True)
            sheet_names = wb.sheetnames
            
            # Get preview data from first sheet
            first_sheet = wb[sheet_names[0]]
            
            # Read first 10 rows for preview
            preview_data = []
            headers = []
            
            for row_idx, row in enumerate(first_sheet.iter_rows(values_only=True)):
                if row_idx == 0:
                    # First row as headers
                    headers = [cell if cell is not None else f"Column_{i+1}" for i, cell in enumerate(row)]
                elif row_idx < 11:  # First 10 data rows
                    row_data = [cell if cell is not None else "" for cell in row]
                    # Pad row to match header length
                    while len(row_data) < len(headers):
                        row_data.append("")
                    preview_data.append(row_data[:len(headers)])  # Trim to header length
                else:
                    break
            
            wb.close()
            
            # Calculate total rows safely (max_row can be None for empty sheets)
            total_rows = (first_sheet.max_row - 1) if first_sheet.max_row else 0
            
            return {
                'success': True,
                'sheet_names': sheet_names,
                'headers': headers,
                'preview_data': preview_data,
                'total_rows': max(total_rows, len(preview_data))  # Use actual data count if max_row is unreliable
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error parsing Excel file: {str(e)}"
            }
    


    def extract_account_ids_from_excel(self, file_content, sheet_name, account_id_column):
        """Extract Account IDs from specified column in Excel file"""
        try:
            # Use pandas for easier data extraction - read as string to preserve Account ID format
            df = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_name, dtype={account_id_column: str})
            
            if account_id_column not in df.columns:
                return {
                    'success': False,
                    'error': f"Column '{account_id_column}' not found in sheet '{sheet_name}'"
                }
            
            # Extract Account IDs and remove null/empty values
            account_ids = df[account_id_column].dropna().astype(str).tolist()
            # Remove empty strings and whitespace-only strings, and handle Excel formatting issues
            cleaned_account_ids = []
            for aid in account_ids:
                aid_str = str(aid).strip()
                # Remove any Excel formatting artifacts
                if aid_str and aid_str.lower() not in ['nan', 'none', 'null']:
                    # Handle potential floating point conversion (e.g., "1.23456789012345e+17")
                    if 'e+' in aid_str.lower():
                        try:
                            # Convert scientific notation back to full number
                            aid_str = f"{float(aid_str):.0f}"
                        except:
                            pass
                    cleaned_account_ids.append(aid_str)
            
            account_ids = cleaned_account_ids
            
            # Get original data for later merging - handle NaN values
            # Replace NaN with empty string to avoid JSON serialization issues
            df_clean = df.where(pd.notnull(df), '')  # Replace NaN with empty string
            original_data = df_clean.to_dict('records')
            
            return {
                'success': True,
                'account_ids': account_ids,
                'original_data': original_data,
                'total_rows': len(df)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error extracting Account IDs: {str(e)}"
            }
    
    def _convert_15_to_18_char_id(self, id_15):
        """Convert 15-character Salesforce ID to 18-character format"""
        if len(id_15) != 15:
            return id_15
        
        # Salesforce ID conversion algorithm
        suffix = ""
        for i in range(3):
            chunk = id_15[i*5:(i+1)*5]
            chunk_value = 0
            for j, char in enumerate(chunk):
                if char.isupper():
                    chunk_value += 2 ** j
            
            # Convert to base-32 character
            if chunk_value < 26:
                suffix += chr(ord('A') + chunk_value)
            else:
                suffix += str(chunk_value - 26)
        
        return id_15 + suffix

    def create_basic_excel(self, data, headers, title="Data Export", filename_prefix="export"):
        """Create a basic Excel file with data and headers"""
        try:
            wb = Workbook()
            ws = wb.active
            if ws is not None:
                ws.title = "Data"
                
                # Add title
                current_row = 1
                ws.merge_cells(f'A{current_row}:{get_column_letter(len(headers))}{current_row}')
                ws[f'A{current_row}'] = title
                ws[f'A{current_row}'].font = self.title_font
                ws[f'A{current_row}'].alignment = self.center_alignment
                current_row += 1
                
                # Add timestamp
                ws.merge_cells(f'A{current_row}:{get_column_letter(len(headers))}{current_row}')
                ws[f'A{current_row}'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ws[f'A{current_row}'].alignment = self.center_alignment
                current_row += 2
                
                # Add headers
                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=current_row, column=col, value=header)
                    cell.font = self.header_font
                    cell.fill = self.header_fill
                    cell.alignment = self.center_alignment
                    cell.border = self.border
                
                current_row += 1
                
                # Add data rows
                for row_data in data:
                    for col, value in enumerate(row_data, 1):
                        cell = ws.cell(row=current_row, column=col, value=value)
                        cell.border = self.border
                    current_row += 1
                
                # Auto-adjust column widths
                for col in range(1, len(headers) + 1):
                    ws.column_dimensions[get_column_letter(col)].width = 20
            
            # Create file buffer
            file_buffer = io.BytesIO()
            wb.save(file_buffer)
            file_buffer.seek(0)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename_prefix}_{timestamp}.xlsx"
            
            return {
                'success': True,
                'file_buffer': file_buffer,
                'filename': filename
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error creating Excel file: {str(e)}"
            } 