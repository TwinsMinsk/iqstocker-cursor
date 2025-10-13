"""CSV parser for Adobe Stock analytics."""

import pandas as pd
from typing import Dict, List, Any
from datetime import datetime


class CSVParser:
    """Parser for Adobe Stock CSV files."""
    
    def __init__(self):
        self.required_columns = ['Title', 'Asset ID', 'Sales', 'Revenue']
        from config.settings import settings
        self.new_works_months = getattr(settings, 'new_works_months', 3)
    
    def parse_csv(self, file_path: str) -> Dict[str, Any]:
        """Parse CSV file and extract sales data."""
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Validate columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Process data
            sales_data = []
            
            for _, row in df.iterrows():
                # Extract basic information
                title = str(row['Title']).strip()
                asset_id = str(row['Asset ID']).strip()
                sales = int(row['Sales']) if pd.notna(row['Sales']) else 0
                revenue = float(row['Revenue']) if pd.notna(row['Revenue']) else 0.0
                
                # Determine if work is new (uploaded within last 3 months)
                is_new_work = self._is_new_work(row)
                
                sales_data.append({
                    'work_id': asset_id,
                    'title': title,
                    'sales': sales,
                    'revenue': revenue,
                    'is_new_work': is_new_work
                })
            
            return {
                'sales_data': sales_data,
                'total_rows': len(df),
                'parsed_at': datetime.utcnow()
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing CSV: {str(e)}")
    
    def _is_new_work(self, row: pd.Series) -> bool:
        """Determine if work is new according to TЗ (ID starts with 150 or upload date)."""
        
        asset_id = str(row.get('Asset ID', '')).strip()
        
        # Priority 1: Check by ID (starts with 150, 10 digits total)
        if asset_id.startswith('150') and len(asset_id) == 10:
            return True
        
        # Priority 2: Check by upload date (if available)
        if 'Upload Date' in row and pd.notna(row['Upload Date']):
            try:
                upload_date = pd.to_datetime(row['Upload Date'])
                months_ago = datetime.utcnow() - pd.Timedelta(days=self.new_works_months * 30)
                return upload_date > months_ago
            except:
                pass
        
        # If no criteria match, assume it's not new
        return False
    
    def validate_csv_format(self, file_path: str) -> bool:
        """Validate CSV file format."""
        
        try:
            df = pd.read_csv(file_path)
            
            # Check required columns
            for col in self.required_columns:
                if col not in df.columns:
                    return False
            
            # Check if file is not empty
            if len(df) == 0:
                return False
            
            return True
            
        except Exception:
            return False