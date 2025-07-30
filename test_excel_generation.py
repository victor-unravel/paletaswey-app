#!/usr/bin/env python3
"""
Test Excel generation functionality
"""

import pandas as pd
import io
import xlsxwriter
from datetime import datetime

def test_excel_generation():
    """Test creating an Excel file from DataFrame"""
    print("Testing Excel generation...")
    
    # Create a sample DataFrame similar to what the app would generate
    sample_data = {
        'Reported on': ['2024-01-16 21:20', '2024-01-15 17:30'],
        'Reported by': ['Jane Smith', 'John Doe'],
        'POS Visit': ['Store Beta Visit', 'Store Alpha Visit'],
        'POS Alternative Import Name': ['ALT002', 'ALT001'],
        'Status': ['reported', 'Validated'],
        'Product A': [2, 5],
        'Product B': ['', 3],
        'Total': [2, 8]
    }
    
    df = pd.DataFrame(sample_data)
    print(f"Created DataFrame with shape: {df.shape}")
    print(df.to_string())
    
    # Test Excel generation
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='POS Visit Recap')
        
        # Access the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['POS Visit Recap']
        
        # Add some formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Apply header formatting
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    buffer.seek(0)
    excel_size = len(buffer.getvalue())
    
    print(f"✅ Excel file generated successfully!")
    print(f"📊 Excel file size: {excel_size} bytes")
    
    # Save to disk for verification
    with open('test_output.xlsx', 'wb') as f:
        f.write(buffer.getvalue())
    print(f"💾 Excel file saved as 'test_output.xlsx'")
    
    return True

def test_pandas_performance():
    """Test pandas operations performance"""
    print("\nTesting pandas performance...")
    
    # Create a larger dataset for performance testing
    import random
    
    large_data = []
    for i in range(1000):
        large_data.append({
            'id': i,
            'timestamp': f'2024-01-{random.randint(1, 30):02d}T{random.randint(0, 23):02d}:00:00Z',
            'product': f'Product {chr(65 + i % 26)}',
            'quantity': random.randint(1, 100),
            'store': f'Store {i % 10}'
        })
    
    start_time = datetime.now()
    df = pd.DataFrame(large_data)
    
    # Perform some operations similar to the app
    grouped = df.groupby(['store', 'product'])['quantity'].sum().reset_index()
    pivoted = grouped.pivot(index='store', columns='product', values='quantity').fillna(0)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"✅ Processed {len(large_data)} records in {duration:.3f} seconds")
    print(f"📊 Final pivoted table shape: {pivoted.shape}")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Excel generation and pandas performance...\n")
    
    try:
        test_excel_generation()
        test_pandas_performance()
        print("\n🎉 All Excel and performance tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()