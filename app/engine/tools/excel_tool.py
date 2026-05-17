async def read_excel(file_path: str, sheet_name: str = "", max_rows: int = 1000) -> list:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        rows = []
        headers = None
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                headers = [str(c) if c is not None else f"col_{j}" for j, c in enumerate(row)]
                continue
            if i > max_rows:
                break
            rows.append(dict(zip(headers or [], [str(c) if c is not None else "" for c in row])))
        return rows
    except Exception as e:
        return [{"error": str(e)}]


async def write_excel(file_path: str, data: list, sheet_name: str = "Sheet1") -> dict:
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        if not data:
            wb.save(file_path)
            return {"rows_written": 0}
        headers = list(data[0].keys())
        ws.append(headers)
        for row in data:
            ws.append([row.get(h, "") for h in headers])
        wb.save(file_path)
        return {"rows_written": len(data), "file": file_path}
    except Exception as e:
        return {"error": str(e)}


async def create_excel(file_path: str, sheets: dict) -> dict:
    """sheets: {sheet_name: [{"col": val, ...}, ...]}"""
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # remove default
        for name, rows in sheets.items():
            ws = wb.create_sheet(name)
            if rows:
                headers = list(rows[0].keys())
                ws.append(headers)
                for row in rows:
                    ws.append([row.get(h, "") for h in headers])
        wb.save(file_path)
        return {"created": file_path, "sheets": list(sheets.keys())}
    except Exception as e:
        return {"error": str(e)}


async def excel_formula(file_path: str, cell: str, formula: str, sheet_name: str = "") -> dict:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        ws[cell] = formula
        wb.save(file_path)
        return {"cell": cell, "formula": formula}
    except Exception as e:
        return {"error": str(e)}


async def excel_chart(file_path: str, sheet_name: str, chart_type: str,
                      data_range: str, title: str = "", position: str = "E1") -> dict:
    try:
        import openpyxl
        from openpyxl.chart import BarChart, LineChart, PieChart, Reference
        wb = openpyxl.load_workbook(file_path)
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active

        chart_map = {"bar": BarChart, "line": LineChart, "pie": PieChart}
        ChartClass = chart_map.get(chart_type.lower(), BarChart)
        chart = ChartClass()
        if title:
            chart.title = title

        # Parse simple range like "A1:B10"
        data = Reference(ws, min_col=1, min_row=1, max_row=ws.max_row, max_col=2)
        chart.add_data(data, titles_from_data=True)
        ws.add_chart(chart, position)
        wb.save(file_path)
        return {"chart_added": True, "type": chart_type, "file": file_path}
    except Exception as e:
        return {"error": str(e)}
