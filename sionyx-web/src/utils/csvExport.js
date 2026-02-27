export const exportToCSV = (data, columns, filename) => {
  if (!data || data.length === 0) return;

  const headers = columns.map(c => c.title).join(',');
  const rows = data.map(row =>
    columns
      .map(c => {
        let val = row[c.dataIndex] ?? '';
        if (typeof val === 'string' && (val.includes(',') || val.includes('"') || val.includes('\n'))) {
          val = `"${val.replace(/"/g, '""')}"`;
        }
        return val;
      })
      .join(',')
  );

  const bom = '\uFEFF';
  const csv = bom + [headers, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename.endsWith('.csv') ? filename : `${filename}.csv`;
  link.click();
  URL.revokeObjectURL(url);
};

/**
 * Export data as Excel-compatible HTML table (.xls)
 * Excel opens HTML tables with .xls extension natively
 */
export const exportToExcel = (data, columns, filename) => {
  if (!data || data.length === 0) return;

  const headers = columns.map(c => c.title);
  const rows = data.map(row =>
    columns.map(c => {
      const val = row[c.dataIndex] ?? '';
      return String(val).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    })
  );

  const headerRow = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
  const dataRows = rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');

  const html = `<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
<head>
<meta charset="UTF-8">
<!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>Sheet1</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->
</head>
<body dir="rtl">
<table border="1">${headerRow}${dataRows}</table>
</body>
</html>`;

  const bom = '\uFEFF';
  const blob = new Blob([bom + html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename.endsWith('.xls') ? filename : `${filename}.xls`;
  link.click();
  URL.revokeObjectURL(url);
};

/**
 * Export data as printable PDF view (opens new window with print dialog)
 */
export const exportToPDF = (data, columns, filename, title = 'ייצוא') => {
  if (!data || data.length === 0) return;

  const headers = columns.map(c => c.title);
  const rows = data.map(row =>
    columns.map(c => {
      const val = row[c.dataIndex] ?? '';
      return String(val).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    })
  );

  const headerRow = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
  const dataRows = rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');

  const html = `<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8">
<title>${title}</title>
<style>
body { font-family: Arial, sans-serif; padding: 20px; direction: rtl; }
h1 { font-size: 18px; margin-bottom: 16px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
th { background: #f5f5f5; font-weight: 600; }
@media print { body { padding: 0; } }
</style>
</head>
<body>
<h1>${title}</h1>
<p>תאריך ייצוא: ${new Date().toLocaleDateString('he-IL')}</p>
<table>${headerRow}${dataRows}</table>
</body>
</html>`;

  const win = window.open('', '_blank');
  win.document.write(html);
  win.document.close();
  win.focus();
  setTimeout(() => {
    win.print();
    win.close();
  }, 250);
};
